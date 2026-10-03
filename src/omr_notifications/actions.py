from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from .models import ActionResult, Event, iso_time
from .policy import MISSING, field_value


TOKEN = re.compile(r"\$\{(event(?:\.[A-Za-z0-9_-]+)+)\}")


def render(value: Any, event: Event) -> Any:
    if isinstance(value, str):
        def replace(match: re.Match[str]) -> str:
            found = field_value(event, match.group(1).removeprefix("event."))
            if found is MISSING:
                return ""
            if isinstance(found, (dict, list, tuple)):
                return json.dumps(found, ensure_ascii=False)
            return str(found)
        return TOKEN.sub(replace, value)
    if isinstance(value, list):
        return [render(item, event) for item in value]
    if isinstance(value, dict):
        return {key: render(item, event) for key, item in value.items()}
    return value


class ActionDispatcher:
    def __init__(
        self,
        *,
        timeout: float = 10.0,
        output_bytes: int = 16 * 1024,
        dry_run: bool = False,
        record: Callable[[Event, str | None, list[dict[str, Any]] | None], None] | None = None,
        set_listener: Callable[[str, bool, Event], bool] | None = None,
    ):
        self.timeout = timeout
        self.output_bytes = output_bytes
        self.dry_run = dry_run
        self.record = record
        self.set_listener = set_listener
        self.notifications: dict[str, int] = {}

    def dispatch(self, action: dict[str, Any], event: Event, policy_id: str) -> ActionResult:
        started = iso_time()
        action_id = str(action.get("id") or uuid4())
        kind = action["type"]
        config = render(action.get("config", {}), event)
        if self.dry_run and kind != "event.record":
            return ActionResult(action_id, kind, "skipped", started, iso_time(), "dry-run")
        try:
            if kind == "notification.show":
                status, message, output = self._notification_show(config)
            elif kind == "notification.dismiss":
                status, message, output = self._notification_dismiss(config)
            elif kind == "osd.show":
                status, message, output = self._osd_show(config)
            elif kind == "sound.play":
                status, message, output = self._sound_play(config)
            elif kind == "exec.argv":
                status, message, output = self._exec_argv(config)
            elif kind in {"listener.enable", "listener.disable"}:
                enabled = kind.endswith("enable")
                changed = bool(self.set_listener and self.set_listener(str(config["listenerId"]), enabled, event))
                status, message, output = "success", ("changed" if changed else "already-set"), ""
            elif kind == "event.record":
                status, message, output = "success", "recorded", ""
            else:
                status, message, output = "failure", "unsupported action", ""
        except subprocess.TimeoutExpired:
            status, message, output = "timed-out", f"exceeded {self.timeout:g}s", ""
        except (OSError, ValueError, KeyError) as error:
            status, message, output = "failure", str(error), ""
        return ActionResult(action_id, kind, status, started, iso_time(), message, output[: self.output_bytes])

    def _run(self, argv: list[str], timeout: float | None = None, cwd: str | None = None) -> tuple[str, str, str]:
        if not argv or not all(isinstance(x, str) and x for x in argv):
            raise ValueError("argv must be a non-empty string array")
        completed = subprocess.run(
            argv,
            cwd=cwd,
            env=os.environ.copy(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=min(float(timeout or self.timeout), self.timeout),
            check=False,
        )
        output = (completed.stdout + completed.stderr).strip()[: self.output_bytes]
        if completed.returncode == 0:
            return "success", "", output
        return "failure", f"exit code {completed.returncode}", output

    def _notification_show(self, config: dict[str, Any]) -> tuple[str, str, str]:
        if not shutil.which("notify-send"):
            return "failure", "notify-send is unavailable", ""
        title = str(config.get("title", "OmR Notifications"))[:256]
        body = str(config.get("body", ""))[:4096]
        argv = ["notify-send", "--app-name=OmR Notifications", "--print-id"]
        urgency = str(config.get("urgency", "normal"))
        if urgency in {"low", "normal", "critical"}:
            argv.append(f"--urgency={urgency}")
        timeout_ms = int(max(0, min(120_000, int(config.get("timeoutMs", 5000)))))
        argv.append(f"--expire-time={timeout_ms}")
        if config.get("icon"):
            argv.extend(["--icon", str(config["icon"])])
        replace_key = str(config.get("replaceKey", ""))
        if replace_key and replace_key in self.notifications:
            argv.extend(["--replace-id", str(self.notifications[replace_key])])
        argv.extend([title, body])
        status, message, output = self._run(argv)
        if status == "failure" and "org.freedesktop.DBus.Error.ServiceUnknown" in output and shutil.which("omarchy-shell"):
            toast_type = {"critical": "error", "normal": "info", "low": "info"}.get(urgency, "info")
            fallback_icon = str(config.get("icon", "notifications_active"))
            fallback = self._run(["omarchy-shell", "omacale", "toast", toast_type, title, body, fallback_icon])
            if fallback[0] == "success":
                return "success", "shown through Omacale toast fallback", fallback[2]
            return fallback
        if status == "success" and replace_key:
            first = output.splitlines()[0] if output else ""
            if first.isdigit():
                self.notifications[replace_key] = int(first)
        return status, message, output

    def _notification_dismiss(self, config: dict[str, Any]) -> tuple[str, str, str]:
        key = str(config.get("replaceKey", ""))
        notification_id = self.notifications.get(key)
        if not key or notification_id is None:
            return "skipped", "no owned notification for replaceKey", ""
        status, message, output = self._run([
            "gdbus", "call", "--session", "--dest", "org.freedesktop.Notifications",
            "--object-path", "/org/freedesktop/Notifications",
            "--method", "org.freedesktop.Notifications.CloseNotification", str(notification_id),
        ])
        if status == "success":
            self.notifications.pop(key, None)
        return status, message, output

    def _osd_show(self, config: dict[str, Any]) -> tuple[str, str, str]:
        if not shutil.which("omarchy-shell"):
            return "failure", "omarchy-shell is unavailable", ""
        payload = json.dumps({
            "icon": str(config.get("icon", "notification")),
            "message": str(config.get("message", ""))[:512],
        })
        return self._run(["omarchy-shell", "shell", "summon", "omarchy.osd", payload])

    def _sound_play(self, config: dict[str, Any]) -> tuple[str, str, str]:
        path = Path(str(config.get("path", ""))).expanduser().resolve(strict=False)
        allowed = [Path(str(item)).expanduser().resolve(strict=False) for item in config.get("allowedRoots", [])]
        if not path.is_file():
            return "failure", "sound path is not a file", ""
        if allowed and not any(path == root or root in path.parents for root in allowed):
            return "failure", "sound path is outside allowed roots", ""
        player = shutil.which("pw-play") or shutil.which("aplay")
        if not player:
            return "failure", "no supported sound player is available", ""
        return self._run([player, str(path)], timeout=float(config.get("timeoutSeconds", self.timeout)))

    def _exec_argv(self, config: dict[str, Any]) -> tuple[str, str, str]:
        argv = config.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x for x in argv):
            raise ValueError("exec.argv requires literal argv")
        if len(argv) > 64 or sum(len(x.encode()) for x in argv) > 16 * 1024:
            raise ValueError("exec.argv exceeds argument bounds")
        cwd = config.get("cwd")
        if cwd is not None:
            cwd = str(Path(str(cwd)).expanduser().resolve(strict=True))
        return self._run(argv, timeout=float(config.get("timeoutSeconds", self.timeout)), cwd=cwd)
