from __future__ import annotations

import json
import errno
import fcntl
import os
import select
import signal
import socket
import time
from collections import deque
from pathlib import Path
from typing import Any

from .actions import ActionDispatcher
from .adapters import AdapterCoordinator, Observation
from .models import ActionResult, Event, EventNormalizer, iso_time
from .paths import RuntimePaths
from .persistence import ConfigManager, Journal, RuntimeState, atomic_write_json
from .policy import Evaluation, PolicyEngine
from .validation import impact_for_listener, preflight


ALREADY_RUNNING = 75


class CompanionRuntime:
    def __init__(self, paths: RuntimePaths, config_path: Path | None = None, dry_run: bool = False):
        self.paths = paths
        self.config_manager = ConfigManager(paths, config_path)
        self.state = RuntimeState(paths)
        self.config, self.config_source = self.config_manager.load_initial()
        self.preflight = preflight(self.config)
        limits = self.config["limits"]
        self.normalizer = EventNormalizer(int(self.state.value.get("sequence", 0)), int(limits["causalDepth"]))
        self.engine = PolicyEngine(self._effective_policies(), int(limits["causalDepth"]))
        self.journal = Journal(paths.journal_file, int(limits["journalRecords"]), int(limits["journalBytes"]))
        self.adapters = AdapterCoordinator(self.state.value)
        self.dispatcher = ActionDispatcher(
            timeout=float(limits["actionTimeoutSeconds"]),
            output_bytes=int(limits["actionOutputBytes"]),
            dry_run=dry_run,
            record=self._record,
            set_listener=self._set_listener,
        )
        self.queue: deque[Event] = deque()
        self.queue_capacity = int(limits["queueCapacity"])
        self.paused = bool(self.state.value.get("paused", self.config.get("paused", False)))
        self.running = False
        self.server: socket.socket | None = None
        self.lock_stream: Any | None = None
        self.started_at = iso_time()
        self.accepted = 0
        self.dropped = 0
        self.suppressed = 0
        self.failed_actions = 0
        self.last_event: dict[str, Any] | None = None
        self.last_error = ""
        self.last_status_write = 0.0
        self.last_state_write = 0.0

    def _effective_policies(self) -> list[dict[str, Any]]:
        acknowledged = set(self.config.get("impactAcknowledgements", []))
        return [
            policy for policy in self.config["policies"]
            if "exec.argv" in acknowledged
            or not any(action.get("type") == "exec.argv" for action in policy.get("actions", []))
        ]

    def _apply_config(self) -> None:
        self.preflight = preflight(self.config)
        limits = self.config["limits"]
        self.queue_capacity = int(limits["queueCapacity"])
        self.normalizer.max_depth = int(limits["causalDepth"])
        self.engine.max_depth = int(limits["causalDepth"])
        self.engine.replace_policies(self._effective_policies())
        self.dispatcher.timeout = float(limits["actionTimeoutSeconds"])
        self.dispatcher.output_bytes = int(limits["actionOutputBytes"])
        self.journal.max_records = int(limits["journalRecords"])
        self.journal.max_bytes = int(limits["journalBytes"])

    def _active_listeners(self) -> list[dict[str, Any]]:
        overrides = self.state.value.get("listenerOverrides", {})
        acknowledged = set(self.config.get("impactAcknowledgements", []))
        output = []
        for listener in self.config["listeners"]:
            enabled = bool(overrides.get(listener["id"], listener.get("enabled", True)))
            if not enabled:
                continue
            impact = impact_for_listener(listener)
            if impact["acknowledgementRequired"] and impact["fingerprint"] not in acknowledged:
                continue
            output.append(listener)
        return output

    def _set_listener(self, listener_id: str, enabled: bool, parent: Event) -> bool:
        if listener_id not in {x["id"] for x in self.config["listeners"]}:
            raise ValueError(f"unknown listener {listener_id!r}")
        overrides = self.state.value.setdefault("listenerOverrides", {})
        current = next(x.get("enabled", True) for x in self.config["listeners"] if x["id"] == listener_id)
        current = overrides.get(listener_id, current)
        if bool(current) == enabled:
            return False
        overrides[listener_id] = enabled
        self.state.save()
        derived = self.normalizer.create(
            event_type="listener.state.changed",
            listener_id=listener_id,
            adapter="runtime",
            data={"enabled": enabled},
            provenance="explicit",
            origin="omr.action.listener",
            correlation_id=parent.correlation_id,
            causation_id=parent.id,
            causal_depth=parent.causal_depth + 1,
        )
        self.accept(derived)
        return True

    def _record(self, event: Event, policy_id: str | None, results: list[dict[str, Any]] | None) -> None:
        retention = self.config.get("retention", {})
        if not retention.get("enabled", True):
            return
        if event.sensitivity == "sensitive" and not retention.get("sensitive", False):
            return
        self.journal.append(event, policy_id, results)

    def accept(self, event: Event) -> bool:
        if len(self.queue) >= self.queue_capacity:
            self.dropped += 1
            return False
        self.queue.append(event)
        self.accepted += 1
        return True

    def _normalize(self, observation: Observation) -> Event:
        return self.normalizer.create(
            event_type=observation.event_type,
            listener_id=observation.listener_id,
            adapter=observation.adapter,
            data=observation.data,
            occurred_at=observation.occurred_at,
            provenance=observation.provenance,
            sensitivity=observation.sensitivity,
            origin=observation.origin,
        )

    def _process_evaluation(self, evaluation: Evaluation) -> bool:
        if evaluation.status != "matched":
            self.suppressed += 1
            return False
        policy = evaluation.policy
        results = []
        successful = False
        error_strategy = policy.get("errorStrategy", "continue")
        for action in policy["actions"]:
            if self.paused and action["type"] != "event.record":
                data = ActionResult(
                    str(action.get("id", "paused")), action["type"], "suppressed",
                    iso_time(), iso_time(), "globally paused",
                ).to_dict()
            else:
                result = self.dispatcher.dispatch(action, evaluation.event, policy["id"])
                data = result.to_dict()
            results.append(data)
            if data["status"] == "success":
                successful = True
            elif data["status"] in {"failure", "timed-out"}:
                self.failed_actions += 1
                if error_strategy in {"stop-policy", "stop-event"}:
                    break
        if successful:
            self.engine.mark_executed(evaluation)
        if any(action["type"] == "event.record" for action in policy["actions"]):
            self._record(evaluation.event, policy["id"], results)
        return error_strategy == "stop-event" and any(item["status"] in {"failure", "timed-out"} for item in results)

    def process_queue(self) -> None:
        while self.queue:
            event = self.queue.popleft()
            self.last_event = event.to_dict()
            evaluations = self.engine.evaluate(event)
            for evaluation in evaluations:
                if self._process_evaluation(evaluation):
                    break
        for evaluation in self.engine.flush_debounced():
            self._process_evaluation(evaluation)

    def _reload(self) -> bool:
        changed = self.config_manager.reload_if_changed(force=True)
        if changed:
            self.config = self.config_manager.active
            self._apply_config()
        return changed

    def _ingress_event(self, raw: dict[str, Any]) -> Event:
        listener_id = str(raw.get("listenerId", ""))
        listener = next((x for x in self._active_listeners() if x["id"] == listener_id), None)
        if not listener or listener["type"] not in {"explicit.ingress", "omarchy.hook"}:
            raise ValueError("listener is not an active ingress listener")
        event_type = str(raw.get("type", ""))
        if not event_type or len(event_type) > 160:
            raise ValueError("type must be a non-empty bounded string")
        config = listener.get("config", {})
        if listener["type"] == "omarchy.hook":
            prefix = "omarchy.hook."
            if not event_type.startswith(prefix) or event_type.removeprefix(prefix) not in config.get("hooks", []):
                raise ValueError("hook event is not allowlisted")
        allowed = config.get("eventTypes", [])
        if allowed and event_type not in allowed:
            raise ValueError("event type is not allowlisted")
        data = raw.get("data", {})
        if not isinstance(data, dict):
            raise ValueError("data must be an object")
        if len(json.dumps(data, ensure_ascii=False).encode()) > int(self.config["limits"]["ingressBytes"]):
            raise ValueError("data exceeds ingress limit")
        return self.normalizer.create(
            event_type=event_type,
            listener_id=listener_id,
            adapter="ingress",
            data=data,
            occurred_at=raw.get("occurredAt"),
            provenance=str(raw.get("provenance", "explicit")),
            sensitivity=str(raw.get("sensitivity", "local")),
            origin=str(raw.get("origin", "ingress.local"))[:160],
            correlation_id=raw.get("correlationId"),
            causation_id=raw.get("causationId"),
            causal_depth=int(raw.get("causalDepth", 0)),
        )

    def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        command = request.get("command")
        if command == "emit":
            event = self._ingress_event(request.get("event", {}))
            accepted = self.accept(event)
            return {"ok": accepted, "eventId": event.id, "sequence": event.sequence}
        if command == "status":
            return {"ok": True, "status": self.status()}
        if command == "pause":
            self.paused = True
            self.state.value["paused"] = True
            self.state.save()
            return {"ok": True, "paused": True}
        if command == "resume":
            self.paused = False
            self.state.value["paused"] = False
            self.state.save()
            return {"ok": True, "paused": False}
        if command == "reload":
            return {"ok": True, "changed": self._reload(), "rejected": self.config_manager.rejected}
        if command == "shutdown":
            self.running = False
            return {"ok": True}
        raise ValueError("unknown command")

    def _open_socket(self) -> None:
        self.paths.runtime_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(str(self.paths.socket_file))
        os.chmod(self.paths.socket_file, 0o600)
        server.listen(8)
        server.setblocking(False)
        self.server = server

    def _acquire_runtime_lock(self) -> bool:
        self.paths.runtime_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        stream = self.paths.lock_file.open("a+", encoding="utf-8")
        os.chmod(self.paths.lock_file, 0o600)
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            stream.close()
            return False
        self.lock_stream = stream
        return True

    def _runtime_already_running(self) -> bool:
        if not self.paths.socket_file.exists():
            return False
        try:
            response = send_request(self.paths, {"command": "status"}, timeout=0.5)
            return bool(response.get("ok"))
        except (ConnectionError, OSError, json.JSONDecodeError):
            self.paths.socket_file.unlink(missing_ok=True)
            return False

    def _serve_one(self) -> None:
        assert self.server is not None
        connection, _ = self.server.accept()
        with connection:
            connection.settimeout(1)
            limit = int(self.config["limits"]["ingressBytes"])
            raw = connection.recv(limit + 1)
            try:
                if len(raw) > limit:
                    raise ValueError("request exceeds ingress limit")
                request = json.loads(raw.decode())
                if not isinstance(request, dict):
                    raise ValueError("request must be an object")
                response = self.handle_request(request)
            except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as error:
                response = {"ok": False, "error": str(error)}
            connection.sendall((json.dumps(response, separators=(",", ":")) + "\n").encode())

    def status(self) -> dict[str, Any]:
        listeners = self._active_listeners()
        return {
            "schemaVersion": 1,
            "running": self.running,
            "pid": os.getpid(),
            "startedAt": self.started_at,
            "updatedAt": iso_time(),
            "paused": self.paused,
            "configRevision": self.config.get("revision", 1),
            "configSource": self.config_source,
            "configRejected": self.config_manager.rejected,
            "listenersConfigured": len(self.config["listeners"]),
            "listenersActive": len(listeners),
            "policiesActive": len(self.engine.policies),
            "queueDepth": len(self.queue),
            "acceptedEvents": self.accepted,
            "droppedEvents": self.dropped,
            "suppressedEvaluations": self.suppressed,
            "failedActions": self.failed_actions,
            "lastEvent": self.last_event,
            "preflight": self.preflight,
            "lastError": self.last_error,
        }

    def publish_status(self, force: bool = False) -> None:
        now = time.monotonic()
        if force or now - self.last_status_write >= 1.0:
            atomic_write_json(self.paths.status_file, self.status())
            self.last_status_write = now
        if force or now - self.last_state_write >= 5.0:
            self.state.value["sequence"] = self.normalizer.sequence
            self.state.save()
            self.last_state_write = now

    def run(self, once: bool = False) -> int:
        if not once:
            if not self._acquire_runtime_lock():
                return ALREADY_RUNNING
            if self._runtime_already_running():
                return ALREADY_RUNNING
        self.running = True
        if not once:
            try:
                self._open_socket()
            except OSError as error:
                if error.errno == errno.EADDRINUSE:
                    return ALREADY_RUNNING
                raise
        previous_handlers = {}
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous_handlers[signum] = signal.getsignal(signum)
            signal.signal(signum, lambda _signum, _frame: setattr(self, "running", False))
        try:
            while self.running:
                now = time.time()
                if self.config_manager.reload_if_changed():
                    self.config = self.config_manager.active
                    self._apply_config()
                for observation in self.adapters.poll(self._active_listeners(), now):
                    self.accept(self._normalize(observation))
                self.process_queue()
                self.state.value["sequence"] = self.normalizer.sequence
                self.publish_status()
                if once:
                    break
                assert self.server is not None
                ready, _, _ = select.select([self.server], [], [], 0.2)
                if ready:
                    self._serve_one()
        except Exception as error:
            self.last_error = str(error)
            self.publish_status(force=True)
            return 1
        finally:
            self.running = False
            self.state.value["sequence"] = self.normalizer.sequence
            self.state.save()
            if self.server:
                self.server.close()
            self.paths.socket_file.unlink(missing_ok=True)
            if self.lock_stream:
                self.lock_stream.close()
                self.lock_stream = None
            self.publish_status(force=True)
            for signum, handler in previous_handlers.items():
                signal.signal(signum, handler)
        return 0


def send_request(paths: RuntimePaths, request: dict[str, Any], timeout: float = 2.0) -> dict[str, Any]:
    if not paths.socket_file.exists():
        raise ConnectionError("OmR runtime is not running")
    raw = json.dumps(request, separators=(",", ":")).encode()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(timeout)
        client.connect(str(paths.socket_file))
        client.sendall(raw)
        response = client.recv(1024 * 1024)
    return json.loads(response.decode())
