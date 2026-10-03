from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .integrations import codex_completion_event
from .models import EventNormalizer
from .paths import RuntimePaths
from .persistence import Journal, atomic_write_json, read_json
from .policy import PolicyEngine
from .runtime import CompanionRuntime, send_request
from .validation import ConfigError, default_config, preflight, validate_config


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schemas"


def print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def load_validated(path: Path) -> dict[str, Any]:
    return validate_config(read_json(path))


def command_config(args: argparse.Namespace, paths: RuntimePaths) -> int:
    if args.config_command == "show-default":
        print_json(default_config())
        return 0
    path = Path(args.path).expanduser() if args.path else paths.config_file
    if args.config_command == "init":
        if path.exists() and not args.force:
            print(f"Refusing to overwrite {path}; use --force", file=sys.stderr)
            return 2
        atomic_write_json(path, default_config())
        print(path)
        return 0
    try:
        config = load_validated(path)
    except (OSError, json.JSONDecodeError, ConfigError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print_json({"ok": True, "path": str(path), "revision": config["revision"]})
    return 0


def command_preflight(args: argparse.Namespace, paths: RuntimePaths) -> int:
    path = Path(args.path).expanduser() if args.path else paths.config_file
    try:
        result = preflight(load_validated(path))
    except (OSError, json.JSONDecodeError, ConfigError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print_json(result)
    return 0 if result["ready"] else 3


def command_emit(args: argparse.Namespace, paths: RuntimePaths) -> int:
    try:
        data = json.loads(args.data)
        if not isinstance(data, dict):
            raise ValueError("--data must decode to an object")
        response = send_request(paths, {
            "command": "emit",
            "event": {
                "type": args.type,
                "listenerId": args.listener,
                "data": data,
                "occurredAt": args.occurred_at,
                "provenance": args.provenance,
                "sensitivity": args.sensitivity,
                "origin": args.origin,
            },
        })
    except (ConnectionError, OSError, json.JSONDecodeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print_json(response)
    return 0 if response.get("ok") else 2


def command_codex_notify(args: argparse.Namespace, paths: RuntimePaths) -> int:
    """Best-effort Codex notifier: never make a completed turn fail."""
    try:
        event = codex_completion_event(json.loads(args.payload))
        if event is not None:
            send_request(paths, {"command": "emit", "event": event})
    except (ConnectionError, OSError, json.JSONDecodeError, ValueError):
        pass
    return 0


def command_status(paths: RuntimePaths) -> int:
    try:
        response = send_request(paths, {"command": "status"})
        print_json(response["status"])
        return 0
    except (ConnectionError, OSError, json.JSONDecodeError, KeyError):
        if paths.status_file.exists():
            print_json(read_json(paths.status_file))
            return 1
        print_json({"running": False, "status": "never-started"})
        return 1


def command_control(command: str, paths: RuntimePaths) -> int:
    try:
        response = send_request(paths, {"command": command})
    except (ConnectionError, OSError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print_json(response)
    return 0 if response.get("ok") else 2


def command_test_policy(args: argparse.Namespace, paths: RuntimePaths) -> int:
    config_path = Path(args.config).expanduser() if args.config else paths.config_file
    try:
        config = load_validated(config_path)
        raw = read_json(Path(args.fixture).expanduser())
        normalizer = EventNormalizer(max_depth=int(config["limits"]["causalDepth"]))
        event = normalizer.create(
            event_type=raw["type"],
            listener_id=raw["listenerId"],
            adapter=raw.get("adapter", "fixture"),
            data=raw.get("data", {}),
            occurred_at=raw.get("occurredAt"),
            observed_at=raw.get("observedAt"),
            provenance=raw.get("provenance", "explicit"),
            sensitivity=raw.get("sensitivity", "local"),
            origin=raw.get("origin", "fixture"),
            correlation_id=raw.get("correlationId"),
            causation_id=raw.get("causationId"),
            causal_depth=int(raw.get("causalDepth", 0)),
        )
        evaluations = PolicyEngine(config["policies"], int(config["limits"]["causalDepth"])).evaluate(event, now=args.now)
    except (OSError, json.JSONDecodeError, ConfigError, KeyError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print_json({
        "event": event.to_dict(),
        "evaluations": [
            {
                "policyId": item.policy.get("id"),
                "status": item.status,
                "reason": item.reason,
                "group": item.group,
                "actions": item.policy.get("actions", []) if item.status == "matched" else [],
            }
            for item in evaluations
        ],
    })
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omr-notifications", description="OmR Notifications Companion runtime")
    commands = parser.add_subparsers(dest="command", required=True)

    run = commands.add_parser("run", help="run the Companion runtime")
    run.add_argument("--config")
    run.add_argument("--once", action="store_true")
    run.add_argument("--dry-run", action="store_true")

    config = commands.add_parser("config", help="initialize or validate configuration")
    config_commands = config.add_subparsers(dest="config_command", required=True)
    init = config_commands.add_parser("init")
    init.add_argument("path", nargs="?")
    init.add_argument("--force", action="store_true")
    validate = config_commands.add_parser("validate")
    validate.add_argument("path", nargs="?")
    config_commands.add_parser("show-default")

    pf = commands.add_parser("preflight", help="show machine-readable resource/privacy impact")
    pf.add_argument("path", nargs="?")

    emit = commands.add_parser("emit", help="submit an event to an allowlisted ingress listener")
    emit.add_argument("type")
    emit.add_argument("--listener", required=True)
    emit.add_argument("--data", default="{}")
    emit.add_argument("--occurred-at")
    emit.add_argument("--provenance", choices=["explicit", "observed", "inferred"], default="explicit")
    emit.add_argument("--sensitivity", choices=["public", "local", "sensitive"], default="local")
    emit.add_argument("--origin", default="ingress.cli")

    codex = commands.add_parser("codex-notify", help="accept Codex agent-turn-complete payloads")
    codex.add_argument("payload")

    commands.add_parser("status")
    commands.add_parser("pause")
    commands.add_parser("resume")
    commands.add_parser("reload")
    commands.add_parser("shutdown")

    journal = commands.add_parser("journal")
    journal.add_argument("--count", type=int, default=20)

    test = commands.add_parser("test-policy", help="evaluate one fixture without dispatching actions")
    test.add_argument("fixture")
    test.add_argument("--config")
    test.add_argument("--now", type=float)

    schemas = commands.add_parser("schemas")
    schemas.add_argument("name", nargs="?")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = RuntimePaths.discover()
    if args.command == "run":
        config_path = Path(args.config).expanduser() if args.config else None
        return CompanionRuntime(paths, config_path, args.dry_run).run(args.once)
    if args.command == "config":
        return command_config(args, paths)
    if args.command == "preflight":
        return command_preflight(args, paths)
    if args.command == "emit":
        return command_emit(args, paths)
    if args.command == "codex-notify":
        return command_codex_notify(args, paths)
    if args.command == "status":
        return command_status(paths)
    if args.command in {"pause", "resume", "reload", "shutdown"}:
        return command_control(args.command, paths)
    if args.command == "journal":
        print_json(Journal(paths.journal_file, 2000, 8 * 1024 * 1024).tail(args.count))
        return 0
    if args.command == "test-policy":
        return command_test_policy(args, paths)
    if args.command == "schemas":
        available = sorted(path.stem for path in SCHEMA_DIR.glob("*.json"))
        if not args.name:
            print_json(available)
            return 0
        path = SCHEMA_DIR / f"{args.name}.json"
        if not path.exists():
            print(f"Unknown schema {args.name!r}", file=sys.stderr)
            return 2
        print(path.read_text(encoding="utf-8"), end="")
        return 0
    return 2
