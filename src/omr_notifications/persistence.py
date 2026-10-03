from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .models import Event, iso_time
from .paths import RuntimePaths
from .validation import ConfigError, default_config, validate_config


def atomic_write_json(path: Path, value: Any, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, raw = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp = Path(raw)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temp, mode)
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


class ConfigManager:
    def __init__(self, paths: RuntimePaths, explicit_path: Path | None = None):
        self.paths = paths
        self.config_path = explicit_path or paths.config_file
        self.active = default_config()
        self.rejected: dict[str, Any] | None = None
        self.mtime_ns: int | None = None

    def load_initial(self) -> tuple[dict[str, Any], str]:
        if self.config_path.exists():
            try:
                return self._activate(read_json(self.config_path)), "configured"
            except (OSError, json.JSONDecodeError, ConfigError) as error:
                self.rejected = {"at": iso_time(), "error": str(error), "path": str(self.config_path)}
        if self.paths.last_good_file.exists():
            try:
                return self._activate(read_json(self.paths.last_good_file), persist=False), "last-known-good"
            except (OSError, json.JSONDecodeError, ConfigError):
                pass
        self.active = default_config()
        return self.active, "empty-default"

    def _activate(self, candidate: Any, persist: bool = True) -> dict[str, Any]:
        validated = validate_config(candidate)
        self.active = validated
        self.rejected = None
        if persist:
            atomic_write_json(self.paths.last_good_file, validated)
        try:
            self.mtime_ns = self.config_path.stat().st_mtime_ns
        except OSError:
            self.mtime_ns = None
        return validated

    def reload_if_changed(self, force: bool = False) -> bool:
        try:
            mtime = self.config_path.stat().st_mtime_ns
        except OSError:
            return False
        if not force and mtime == self.mtime_ns:
            return False
        try:
            candidate = read_json(self.config_path)
            self._activate(candidate)
            return True
        except (OSError, json.JSONDecodeError, ConfigError) as error:
            self.mtime_ns = mtime
            self.rejected = {"at": iso_time(), "error": str(error), "path": str(self.config_path)}
            return False


class RuntimeState:
    def __init__(self, paths: RuntimePaths):
        self.paths = paths
        self.value: dict[str, Any] = {
            "schemaVersion": 1,
            "sequence": 0,
            "paused": False,
            "listenerOverrides": {},
            "time": {},
        }
        if paths.runtime_state_file.exists():
            try:
                loaded = read_json(paths.runtime_state_file)
                if isinstance(loaded, dict) and loaded.get("schemaVersion") == 1:
                    self.value.update(loaded)
            except (OSError, json.JSONDecodeError):
                pass

    def save(self) -> None:
        atomic_write_json(self.paths.runtime_state_file, self.value)


class Journal:
    def __init__(self, path: Path, max_records: int, max_bytes: int):
        self.path = path
        self.max_records = max_records
        self.max_bytes = max_bytes
        self._since_prune = 0

    def append(self, event: Event, policy_id: str | None = None, results: list[dict[str, Any]] | None = None) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        record = {"event": event.to_dict(), "policyId": policy_id, "results": results or []}
        raw = json.dumps(record, separators=(",", ":"), ensure_ascii=False)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(raw + "\n")
        os.chmod(self.path, 0o600)
        self._since_prune += 1
        if self._since_prune >= 32 or self.path.stat().st_size > self.max_bytes:
            self.prune()

    def prune(self) -> None:
        self._since_prune = 0
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return
        lines = lines[-self.max_records :]
        while lines and sum(len(line.encode()) + 1 for line in lines) > self.max_bytes:
            lines.pop(0)
        temp_value = "\n".join(lines) + ("\n" if lines else "")
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd, raw = tempfile.mkstemp(prefix=".events.", dir=self.path.parent)
        temp = Path(raw)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(temp_value)
            os.chmod(temp, 0o600)
            os.replace(temp, self.path)
        finally:
            temp.unlink(missing_ok=True)

    def tail(self, count: int = 20) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        records = []
        for line in self.path.read_text(encoding="utf-8").splitlines()[-max(0, count) :]:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return records
