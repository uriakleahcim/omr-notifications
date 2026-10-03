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


def _validate_text(config: dict[str, Any], key: str, path: str, errors: list[str], *, nonempty: bool = False) -> None:
    if key not in config:
        return
    value = config[key]
    if not isinstance(value, str) or "\0" in value or (nonempty and not value.strip()):
        qualifier = "non-empty " if nonempty else ""
        errors.append(f"{path}.{key} must be a {qualifier}string without NUL bytes")


def _validate_literal_argv(value: Any, path: str, errors: list[str]) -> None:
    valid = (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and "\0" not in item for item in value)
        and bool(value[0])
    )
    if not valid:
        errors.append(f"{path} must be a non-empty string array without NUL bytes")
        return
    if len(value) > 64 or sum(len(item.encode()) for item in value) > 16 * 1024:
        errors.append(f"{path} exceeds 64 arguments or 16 KiB")


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
        _validate_literal_argv(argv, f"{path}.config.argv", errors)
        if config.get("shell") is not None:
            errors.append(f"{path}.config.shell is forbidden")
    if kind == "notification.show":
        allowed = {
            "title", "body", "glyph", "urgency", "timeoutMs", "icon", "image",
            "appName", "replaceKey", "onClickArgv",
        }
        unknown = sorted(set(config) - allowed)
        if unknown:
            errors.append(f"{path}.config has unsupported keys: {', '.join(unknown)}")
        _validate_text(config, "title", f"{path}.config", errors, nonempty=True)
        _validate_text(config, "body", f"{path}.config", errors)
        for key in ("glyph", "icon", "image", "appName", "replaceKey"):
            _validate_text(config, key, f"{path}.config", errors, nonempty=True)
        if config.get("urgency", "normal") not in {"low", "normal", "critical"}:
            errors.append(f"{path}.config.urgency must be low, normal, or critical")
        timeout_ms = config.get("timeoutMs", 5000)
        if type(timeout_ms) is not int or not -1 <= timeout_ms <= 2_147_483_647:
            errors.append(f"{path}.config.timeoutMs must be an integer from -1 through 2147483647")
        if "onClickArgv" in config:
            _validate_literal_argv(config["onClickArgv"], f"{path}.config.onClickArgv", errors)
    if kind == "notification.dismiss":
        if set(config) - {"replaceKey"}:
            errors.append(f"{path}.config only supports replaceKey")
        _validate_text(config, "replaceKey", f"{path}.config", errors, nonempty=True)
        if "replaceKey" not in config:
            errors.append(f"{path}.config.replaceKey is required")
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
        or (a.get("type") == "notification.show" and bool(a.get("config", {}).get("onClickArgv")))
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
