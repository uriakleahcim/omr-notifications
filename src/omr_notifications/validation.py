from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from .constants import (
    ACTION_TYPES,
    CONFIG_VERSION,
    DEFAULT_LIMITS,
    ERROR_STRATEGIES,
    LISTENER_TYPES,
)


class ConfigError(ValueError):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


def default_config() -> dict[str, Any]:
    return {
        "schemaVersion": CONFIG_VERSION,
        "revision": 1,
        "paused": False,
        "limits": dict(DEFAULT_LIMITS),
        "retention": {"enabled": True, "sensitive": False},
        "listeners": [],
        "policies": [],
        "impactAcknowledgements": [],
    }


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def impact_fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def _plain_object(value: Any) -> bool:
    return isinstance(value, dict)


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _positive(value: Any) -> bool:
    return _number(value) and value > 0


def _validate_listener(listener: Any, i: int, errors: list[str]) -> None:
    path = f"listeners[{i}]"
    if not _plain_object(listener):
        errors.append(f"{path} must be an object")
        return
    listener_id = listener.get("id")
    if not isinstance(listener_id, str) or not listener_id.strip():
        errors.append(f"{path}.id must be a non-empty string")
    kind = listener.get("type")
    if kind not in LISTENER_TYPES:
        errors.append(f"{path}.type is unsupported: {kind!r}")
    if not isinstance(listener.get("enabled", True), bool):
        errors.append(f"{path}.enabled must be boolean")
    config = listener.get("config", {})
    if not _plain_object(config):
        errors.append(f"{path}.config must be an object")
        return
    if kind == "time.after" and not _positive(config.get("seconds")):
        errors.append(f"{path}.config.seconds must be positive")
    if kind == "time.at" and not isinstance(config.get("at"), str):
        errors.append(f"{path}.config.at must be an ISO-8601 string")
    elif kind == "time.at":
        try:
            datetime.fromisoformat(config["at"].replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"{path}.config.at must be a valid ISO-8601 string")
    if kind == "time.schedule":
        if not _positive(config.get("intervalSeconds")):
            errors.append(f"{path}.config.intervalSeconds must be positive")
        if config.get("missed", "skip") not in {"skip", "once", "all-bounded"}:
            errors.append(f"{path}.config.missed must be skip, once, or all-bounded")
    if kind in {"filesystem.watch", "trash.watch", "screenshot.watch"}:
        roots = config.get("roots")
        if not isinstance(roots, list) or not roots or not all(isinstance(x, str) and x for x in roots):
            errors.append(f"{path}.config.roots must be a non-empty string array")
        if not _positive(config.get("pollSeconds", 1.0)):
            errors.append(f"{path}.config.pollSeconds must be positive")
    if kind == "omarchy.hook":
        hooks = config.get("hooks", [])
        if not isinstance(hooks, list) or not all(isinstance(x, str) and x for x in hooks):
            errors.append(f"{path}.config.hooks must be a string array")


def _validate_condition(condition: Any, path: str, errors: list[str]) -> None:
    operators = {"eq", "ne", "contains", "prefix", "suffix", "glob", "in", "exists", "gt", "gte", "lt", "lte"}
    if not _plain_object(condition):
        errors.append(f"{path} must be an object")
        return
    if not isinstance(condition.get("field"), str) or not condition.get("field"):
        errors.append(f"{path}.field must be a non-empty string")
    if condition.get("operator") not in operators:
        errors.append(f"{path}.operator is unsupported")
    if condition.get("operator") != "exists" and "value" not in condition:
        errors.append(f"{path}.value is required")


def _validate_action(action: Any, path: str, errors: list[str]) -> None:
    if not _plain_object(action):
        errors.append(f"{path} must be an object")
        return
    kind = action.get("type")
    if kind not in ACTION_TYPES:
        errors.append(f"{path}.type is unsupported: {kind!r}")
        return
    if "id" in action and (not isinstance(action["id"], str) or not action["id"]):
        errors.append(f"{path}.id must be a non-empty string")
    config = action.get("config", {})
    if not _plain_object(config):
        errors.append(f"{path}.config must be an object")
        return
    if kind == "exec.argv":
        argv = config.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x for x in argv):
            errors.append(f"{path}.config.argv must be a non-empty string array")
        if config.get("shell") is not None:
            errors.append(f"{path}.config.shell is forbidden")
    if kind in {"listener.enable", "listener.disable"} and not isinstance(config.get("listenerId"), str):
        errors.append(f"{path}.config.listenerId is required")


def _validate_policy(policy: Any, i: int, errors: list[str]) -> None:
    path = f"policies[{i}]"
    if not _plain_object(policy):
        errors.append(f"{path} must be an object")
        return
    if not isinstance(policy.get("id"), str) or not policy.get("id"):
        errors.append(f"{path}.id must be a non-empty string")
    if not isinstance(policy.get("priority", 0), int):
        errors.append(f"{path}.priority must be an integer")
    if not isinstance(policy.get("enabled", True), bool):
        errors.append(f"{path}.enabled must be boolean")
    trigger = policy.get("trigger")
    if not _plain_object(trigger):
        errors.append(f"{path}.trigger must be an object")
    else:
        types = trigger.get("types")
        if not isinstance(types, list) or not types or not all(isinstance(x, str) and x for x in types):
            errors.append(f"{path}.trigger.types must be a non-empty string array")
        listener_ids = trigger.get("listenerIds", [])
        if not isinstance(listener_ids, list) or not all(isinstance(x, str) and x for x in listener_ids):
            errors.append(f"{path}.trigger.listenerIds must be a string array")
    for j, condition in enumerate(policy.get("conditions", [])):
        _validate_condition(condition, f"{path}.conditions[{j}]", errors)
    controls = policy.get("controls", {})
    if not _plain_object(controls):
        errors.append(f"{path}.controls must be an object")
    else:
        for key in ("debounceSeconds", "cooldownSeconds"):
            if key in controls and (not _number(controls[key]) or controls[key] < 0):
                errors.append(f"{path}.controls.{key} must be non-negative")
        if "rateLimit" in controls:
            rate = controls["rateLimit"]
            if not _plain_object(rate) or not isinstance(rate.get("count"), int) or rate.get("count", 0) < 1 or not _positive(rate.get("windowSeconds")):
                errors.append(f"{path}.controls.rateLimit requires positive count and windowSeconds")
    actions = policy.get("actions")
    if not isinstance(actions, list) or not actions:
        errors.append(f"{path}.actions must be a non-empty array")
    else:
        for j, action in enumerate(actions):
            _validate_action(action, f"{path}.actions[{j}]", errors)
    if policy.get("errorStrategy", "continue") not in ERROR_STRATEGIES:
        errors.append(f"{path}.errorStrategy is unsupported")


def validate_config(candidate: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not _plain_object(candidate):
        raise ConfigError(["configuration must be an object"])
    if candidate.get("schemaVersion") != CONFIG_VERSION:
        errors.append(f"schemaVersion must equal {CONFIG_VERSION}")
    if not isinstance(candidate.get("revision", 1), int) or candidate.get("revision", 1) < 1:
        errors.append("revision must be a positive integer")
    listeners = candidate.get("listeners")
    policies = candidate.get("policies")
    if not isinstance(listeners, list):
        errors.append("listeners must be an array")
        listeners = []
    if not isinstance(policies, list):
        errors.append("policies must be an array")
        policies = []
    for i, listener in enumerate(listeners):
        _validate_listener(listener, i, errors)
    for i, policy in enumerate(policies):
        _validate_policy(policy, i, errors)
    listener_ids = [x.get("id") for x in listeners if isinstance(x, dict) and isinstance(x.get("id"), str)]
    policy_ids = [x.get("id") for x in policies if isinstance(x, dict) and isinstance(x.get("id"), str)]
    for label, ids in (("listener", listener_ids), ("policy", policy_ids)):
        duplicates = sorted({x for x in ids if ids.count(x) > 1})
        if duplicates:
            errors.append(f"duplicate {label} ids: {', '.join(duplicates)}")
    known = set(listener_ids)
    for i, policy in enumerate(policies):
        if not isinstance(policy, dict):
            continue
        trigger = policy.get("trigger", {})
        for listener_id in trigger.get("listenerIds", []) if isinstance(trigger, dict) else []:
            if listener_id not in known:
                errors.append(f"policies[{i}] references unknown listener {listener_id!r}")
        for j, action in enumerate(policy.get("actions", [])):
            if isinstance(action, dict) and action.get("type") in {"listener.enable", "listener.disable"}:
                target = action.get("config", {}).get("listenerId")
                if target not in known:
                    errors.append(f"policies[{i}].actions[{j}] references unknown listener {target!r}")
    limits = candidate.get("limits", {})
    if limits and not isinstance(limits, dict):
        errors.append("limits must be an object")
    elif isinstance(limits, dict):
        for key, default in DEFAULT_LIMITS.items():
            value = limits.get(key, default)
            if not _positive(value):
                errors.append(f"limits.{key} must be positive")
    retention = candidate.get("retention", {})
    if not isinstance(retention, dict):
        errors.append("retention must be an object")
    elif not isinstance(retention.get("enabled", True), bool) or not isinstance(retention.get("sensitive", False), bool):
        errors.append("retention.enabled and retention.sensitive must be boolean")
    acknowledgements = candidate.get("impactAcknowledgements", [])
    if not isinstance(acknowledgements, list) or not all(isinstance(item, str) and item for item in acknowledgements):
        errors.append("impactAcknowledgements must be a string array")
    if errors:
        raise ConfigError(errors)
    result = default_config()
    result.update(candidate)
    merged_limits = dict(DEFAULT_LIMITS)
    merged_limits.update(candidate.get("limits", {}))
    result["limits"] = merged_limits
    return result


def impact_for_listener(listener: dict[str, Any]) -> dict[str, Any]:
    kind = listener["type"]
    config = listener.get("config", {})
    roots = [str(Path(os.path.expandvars(os.path.expanduser(p))).resolve(strict=False)) for p in config.get("roots", [])]
    data_classes: list[str] = []
    resident = kind not in {"time.at", "time.after"}
    polling = None
    watches = 0
    sensitive = False
    if kind in {"filesystem.watch", "trash.watch", "screenshot.watch"}:
        data_classes = ["paths", "names", "timestamps", "file-metadata"]
        polling = float(config.get("pollSeconds", 1.0))
        watches = len(roots)
        sensitive = True
    elif kind == "media.mpris":
        data_classes = ["application-identity", "media-metadata", "playback-state"]
        polling = float(config.get("pollSeconds", 1.0))
    elif kind in {"omarchy.hook", "explicit.ingress"}:
        data_classes = ["submitted-metadata"]
    descriptor = {
        "schemaVersion": 1,
        "listenerId": listener["id"],
        "listenerType": kind,
        "resident": resident,
        "sharedRuntime": kind in {"filesystem.watch", "trash.watch", "screenshot.watch", "media.mpris"},
        "pollSeconds": polling,
        "configuredRoots": roots,
        "estimatedWatchRoots": watches,
        "residentChildProcesses": 0,
        "maySpawnTransientProcesses": False,
        "requiresPrivileges": False,
        "dataClasses": data_classes,
        "capturesContent": False,
        "sensitive": sensitive,
        "recursive": bool(config.get("recursive", False)),
    }
    descriptor["fingerprint"] = impact_fingerprint(descriptor)
    descriptor["acknowledgementRequired"] = bool(
        sensitive
        or descriptor["recursive"]
        or (polling is not None and polling < 1.0)
    )
    return descriptor


def preflight(config: dict[str, Any]) -> dict[str, Any]:
    descriptors = [impact_for_listener(x) for x in config["listeners"] if x.get("enabled", True)]
    command_actions = any(
        a.get("type") == "exec.argv"
        for p in config["policies"]
        for a in p.get("actions", [])
    )
    acknowledged = set(config.get("impactAcknowledgements", []))
    missing = [d["fingerprint"] for d in descriptors if d["acknowledgementRequired"] and d["fingerprint"] not in acknowledged]
    if command_actions and "exec.argv" not in acknowledged:
        missing.append("exec.argv")
    return {
        "schemaVersion": 1,
        "listeners": descriptors,
        "commandActions": command_actions,
        "missingAcknowledgements": missing,
        "ready": not missing,
    }
