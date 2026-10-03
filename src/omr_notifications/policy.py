from __future__ import annotations

import fnmatch
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

from .models import Event, thaw


MISSING = object()


def _event_view(event: Event) -> dict[str, Any]:
    return event.to_dict()


def field_value(event: Event, path: str) -> Any:
    current: Any = _event_view(event)
    for part in path.split("."):
        if part in {"__class__", "__dict__", "__proto__"}:
            return MISSING
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, (list, tuple)) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
        else:
            return MISSING
    return current


def condition_matches(event: Event, condition: dict[str, Any]) -> bool:
    actual = field_value(event, condition["field"])
    op = condition["operator"]
    expected = condition.get("value")
    if op == "exists":
        return (actual is not MISSING) is bool(expected if "value" in condition else True)
    if actual is MISSING:
        return False
    if op == "eq":
        return actual == expected
    if op == "ne":
        return actual != expected
    if op == "contains":
        return expected in actual if isinstance(actual, (str, list, tuple, dict)) else False
    if op == "prefix":
        return str(actual).startswith(str(expected))
    if op == "suffix":
        return str(actual).endswith(str(expected))
    if op == "glob":
        return fnmatch.fnmatchcase(str(actual), str(expected))
    if op == "in":
        return actual in expected if isinstance(expected, (list, tuple, str, dict)) else False
    if op in {"gt", "gte", "lt", "lte"}:
        try:
            return {"gt": actual > expected, "gte": actual >= expected, "lt": actual < expected, "lte": actual <= expected}[op]
        except TypeError:
            return False
    return False


def trigger_matches(event: Event, policy: dict[str, Any]) -> bool:
    trigger = policy["trigger"]
    if event.type not in trigger["types"]:
        return False
    if trigger.get("listenerIds") and event.listener_id not in trigger["listenerIds"]:
        return False
    if trigger.get("origins") and event.origin not in trigger["origins"]:
        return False
    if event.origin.startswith("omr.action") and not trigger.get("allowSelf", False):
        return False
    return all(condition_matches(event, condition) for condition in policy.get("conditions", []))


def policy_order(policies: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        (p for p in policies if p.get("enabled", True)),
        key=lambda p: (-int(p.get("priority", 0)), str(p["id"])),
    )


def group_key(event: Event, policy: dict[str, Any]) -> str:
    fields = policy.get("controls", {}).get("groupBy", [])
    if not fields:
        return "*"
    values = []
    for field in fields:
        value = field_value(event, field)
        values.append("<missing>" if value is MISSING else repr(thaw(value)))
    return "|".join(values)


@dataclass(frozen=True)
class Evaluation:
    policy: dict[str, Any]
    event: Event
    group: str
    status: str = "matched"
    reason: str = ""


class PolicyEngine:
    def __init__(self, policies: list[dict[str, Any]], max_depth: int = 8):
        self.policies = policy_order(policies)
        self.max_depth = max_depth
        self.cooldowns: dict[tuple[str, str], float] = {}
        self.rates: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self.debounced: dict[tuple[str, str], tuple[float, Event, dict[str, Any]]] = {}

    def replace_policies(self, policies: list[dict[str, Any]]) -> None:
        self.policies = policy_order(policies)

    @staticmethod
    def _timestamp(now: datetime | float | None) -> float:
        if now is None:
            return datetime.now(timezone.utc).timestamp()
        if isinstance(now, datetime):
            return now.timestamp()
        return float(now)

    def evaluate(self, event: Event, now: datetime | float | None = None) -> list[Evaluation]:
        stamp = self._timestamp(now)
        output: list[Evaluation] = []
        if event.causal_depth >= self.max_depth:
            return [Evaluation({}, event, "*", "suppressed", "causal-depth")]
        for policy in self.policies:
            if not trigger_matches(event, policy):
                continue
            group = group_key(event, policy)
            key = (policy["id"], group)
            controls = policy.get("controls", {})
            cooldown = float(controls.get("cooldownSeconds", 0))
            if cooldown and stamp < self.cooldowns.get(key, 0):
                output.append(Evaluation(policy, event, group, "suppressed", "cooldown"))
                if policy.get("terminal", False):
                    break
                continue
            rate = controls.get("rateLimit")
            if rate:
                history = self.rates[key]
                cutoff = stamp - float(rate["windowSeconds"])
                while history and history[0] <= cutoff:
                    history.popleft()
                if len(history) >= int(rate["count"]):
                    output.append(Evaluation(policy, event, group, "suppressed", "rate-limit"))
                    if policy.get("terminal", False):
                        break
                    continue
            debounce = float(controls.get("debounceSeconds", 0))
            if debounce:
                self.debounced[key] = (stamp + debounce, event, policy)
                output.append(Evaluation(policy, event, group, "deferred", "debounce"))
            else:
                output.append(Evaluation(policy, event, group))
            if policy.get("terminal", False):
                break
        return output

    def flush_debounced(self, now: datetime | float | None = None) -> list[Evaluation]:
        stamp = self._timestamp(now)
        ready: list[Evaluation] = []
        for key, (due, event, policy) in sorted(self.debounced.items()):
            if due <= stamp:
                ready.append(Evaluation(policy, event, key[1]))
        for evaluation in ready:
            self.debounced.pop((evaluation.policy["id"], evaluation.group), None)
        return ready

    def mark_executed(self, evaluation: Evaluation, now: datetime | float | None = None) -> None:
        stamp = self._timestamp(now)
        key = (evaluation.policy["id"], evaluation.group)
        controls = evaluation.policy.get("controls", {})
        cooldown = float(controls.get("cooldownSeconds", 0))
        if cooldown:
            self.cooldowns[key] = stamp + cooldown
        if controls.get("rateLimit"):
            self.rates[key].append(stamp)
