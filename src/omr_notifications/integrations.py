from __future__ import annotations

from pathlib import Path
from typing import Any


def _bounded_text(value: Any, limit: int) -> str:
    if not isinstance(value, str):
        return ""
    return value.replace("\0", "").replace("\r", " ").replace("\n", " ")[:limit]


def codex_completion_event(payload: Any) -> dict[str, Any] | None:
    """Map Codex's notifier payload to a minimal, privacy-preserving OmR event."""
    if not isinstance(payload, dict):
        raise ValueError("Codex notification payload must be an object")
    if payload.get("type") != "agent-turn-complete":
        return None

    cwd = _bounded_text(payload.get("cwd"), 4096)
    project = (Path(cwd).name or cwd) if cwd else "Codex session"
    return {
        "type": "codex.agent-turn-complete",
        "listenerId": "codex-cli",
        "data": {
            "project": project,
            "cwd": cwd,
            "threadId": _bounded_text(payload.get("thread-id"), 160),
            "turnId": _bounded_text(payload.get("turn-id"), 160),
        },
        "provenance": "explicit",
        "sensitivity": "local",
        "origin": "integration.codex-cli",
    }
