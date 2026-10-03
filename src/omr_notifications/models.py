from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from types import MappingProxyType
from typing import Any, Mapping
from uuid import uuid4

from .constants import ACTION_RESULT_VERSION, EVENT_VERSION


EVENT_TYPE = re.compile(r"^[a-z0-9]+(?:[.-][a-z0-9]+)+$")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_time(value: datetime | None = None) -> str:
    return (value or utc_now()).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({str(k): freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(freeze(v) for v in value)
    return value


def thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): thaw(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [thaw(v) for v in value]
    return value


@dataclass(frozen=True)
class Event:
    id: str
    sequence: int
    type: str
    listener_id: str
    adapter: str
    occurred_at: str | None
    observed_at: str
    provenance: str
    sensitivity: str
    origin: str
    correlation_id: str
    causation_id: str | None
    causal_depth: int
    data: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    schema_version: int = EVENT_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": self.schema_version,
            "id": self.id,
            "sequence": self.sequence,
            "type": self.type,
            "listenerId": self.listener_id,
            "adapter": self.adapter,
            "occurredAt": self.occurred_at,
            "observedAt": self.observed_at,
            "provenance": self.provenance,
            "sensitivity": self.sensitivity,
            "origin": self.origin,
            "correlationId": self.correlation_id,
            "causationId": self.causation_id,
            "causalDepth": self.causal_depth,
            "data": thaw(self.data),
        }


@dataclass(frozen=True)
class ActionResult:
    action_id: str
    action_type: str
    status: str
    started_at: str
    finished_at: str
    message: str = ""
    output: str = ""
    schema_version: int = ACTION_RESULT_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": self.schema_version,
            "actionId": self.action_id,
            "actionType": self.action_type,
            "status": self.status,
            "startedAt": self.started_at,
            "finishedAt": self.finished_at,
            "message": self.message,
            "output": self.output,
        }


class EventNormalizer:
    def __init__(self, initial_sequence: int = 0, max_depth: int = 8):
        self.sequence = initial_sequence
        self.max_depth = max_depth

    def create(
        self,
        *,
        event_type: str,
        listener_id: str,
        adapter: str,
        data: dict[str, Any] | None = None,
        occurred_at: str | None = None,
        provenance: str = "observed",
        sensitivity: str = "local",
        origin: str = "adapter",
        correlation_id: str | None = None,
        causation_id: str | None = None,
        causal_depth: int = 0,
        observed_at: str | None = None,
    ) -> Event:
        if not EVENT_TYPE.fullmatch(event_type) or len(event_type) > 160:
            raise ValueError("event type must be a bounded dotted identifier")
        if provenance not in {"explicit", "observed", "inferred"}:
            raise ValueError("invalid event provenance")
        if sensitivity not in {"public", "local", "sensitive"}:
            raise ValueError("invalid event sensitivity")
        if not origin or len(origin) > 160:
            raise ValueError("origin must be a non-empty bounded string")
        if causal_depth < 0 or causal_depth > self.max_depth:
            raise ValueError(f"causal depth must be between 0 and {self.max_depth}")
        self.sequence += 1
        event_id = str(uuid4())
        return Event(
            id=event_id,
            sequence=self.sequence,
            type=event_type,
            listener_id=listener_id,
            adapter=adapter,
            occurred_at=occurred_at,
            observed_at=observed_at or iso_time(),
            provenance=provenance,
            sensitivity=sensitivity,
            origin=origin,
            correlation_id=correlation_id or event_id,
            causation_id=causation_id,
            causal_depth=causal_depth,
            data=freeze(data or {}),
        )
