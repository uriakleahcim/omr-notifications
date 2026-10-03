from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimePaths:
    config_dir: Path
    state_dir: Path
    cache_dir: Path
    runtime_dir: Path

    @classmethod
    def discover(cls) -> "RuntimePaths":
        home = Path.home()
        config_home = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
        state_home = Path(os.environ.get("XDG_STATE_HOME", home / ".local/state"))
        cache_home = Path(os.environ.get("XDG_CACHE_HOME", home / ".cache"))
        runtime_home = Path(os.environ.get("XDG_RUNTIME_DIR", f"/tmp/omr-{os.getuid()}"))
        return cls(
            Path(os.environ.get("OMR_CONFIG_DIR", config_home / "omr-notifications")),
            Path(os.environ.get("OMR_STATE_DIR", state_home / "omr-notifications")),
            Path(os.environ.get("OMR_CACHE_DIR", cache_home / "omr-notifications")),
            Path(os.environ.get("OMR_RUNTIME_DIR", runtime_home / "omr-notifications")),
        )

    @property
    def config_file(self) -> Path:
        return self.config_dir / "config.json"

    @property
    def last_good_file(self) -> Path:
        return self.state_dir / "last-known-good.json"

    @property
    def runtime_state_file(self) -> Path:
        return self.state_dir / "runtime.json"

    @property
    def journal_file(self) -> Path:
        return self.state_dir / "events.jsonl"

    @property
    def socket_file(self) -> Path:
        return self.runtime_dir / "control.sock"

    @property
    def lock_file(self) -> Path:
        return self.runtime_dir / "runtime.lock"

    @property
    def status_file(self) -> Path:
        return self.runtime_dir / "status.json"
