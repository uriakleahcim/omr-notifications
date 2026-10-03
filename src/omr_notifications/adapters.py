from __future__ import annotations

import fnmatch
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import iso_time


@dataclass(frozen=True)
class Observation:
    event_type: str
    listener_id: str
    adapter: str
    data: dict[str, Any]
    occurred_at: str | None = None
    provenance: str = "observed"
    sensitivity: str = "local"
    origin: str = "adapter"


def parse_time(value: str) -> float:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.now().astimezone().tzinfo)
    return parsed.astimezone(timezone.utc).timestamp()


class TimeAdapter:
    def __init__(self, state: dict[str, Any]):
        self.state = state.setdefault("time", {})

    def poll(self, listeners: list[dict[str, Any]], now: float) -> list[Observation]:
        output: list[Observation] = []
        active_ids = set()
        for listener in listeners:
            kind = listener["type"]
            if kind not in {"time.after", "time.at", "time.schedule"}:
                continue
            listener_id = listener["id"]
            active_ids.add(listener_id)
            config = listener.get("config", {})
            item = self.state.setdefault(listener_id, {})
            if kind == "time.after":
                if "due" not in item:
                    item["due"] = now + float(config["seconds"])
                if not item.get("fired") and now >= float(item["due"]):
                    item["fired"] = True
                    output.append(self._observation(listener, "time.after", float(item["due"]), False))
            elif kind == "time.at":
                due = parse_time(config["at"])
                item["due"] = due
                if not item.get("fired") and now >= due:
                    missed = now - due > float(config.get("missedGraceSeconds", 60))
                    if not missed or config.get("missed", "once") == "once":
                        output.append(self._observation(listener, "time.at", due, missed))
                    item["fired"] = True
            else:
                interval = float(config["intervalSeconds"])
                due = float(item.setdefault("due", now + interval))
                if now >= due:
                    missed_count = max(0, int((now - due) // interval))
                    missed_policy = config.get("missed", "skip")
                    count = 1
                    if missed_policy == "all-bounded":
                        count = min(1 + missed_count, int(config.get("maxCatchUp", 10)))
                    elif missed_policy == "skip" and missed_count:
                        count = 0
                    for index in range(count):
                        scheduled = due + interval * index
                        output.append(self._observation(listener, "time.schedule", scheduled, scheduled < now - 0.5))
                    item["due"] = due + interval * (missed_count + 1)
        for stale in set(self.state) - active_ids:
            self.state.pop(stale, None)
        return output

    @staticmethod
    def _observation(listener: dict[str, Any], event_type: str, due: float, missed: bool) -> Observation:
        occurred = iso_time(datetime.fromtimestamp(due, timezone.utc))
        return Observation(
            event_type,
            listener["id"],
            "time",
            {"scheduledFor": occurred, "missed": missed},
            occurred_at=occurred,
            provenance="explicit",
            origin="adapter.time",
        )


@dataclass(frozen=True)
class FileMeta:
    inode: tuple[int, int]
    size: int
    mtime_ns: int
    is_dir: bool


def _excluded(path: Path, root: Path, patterns: list[str]) -> bool:
    relative = str(path.relative_to(root))
    return any(fnmatch.fnmatchcase(relative, pattern) or fnmatch.fnmatchcase(path.name, pattern) for pattern in patterns)


def scan_root(root: Path, recursive: bool, excludes: list[str], max_entries: int) -> tuple[dict[str, FileMeta], str | None]:
    result: dict[str, FileMeta] = {}
    if not root.exists():
        return result, "root-missing"
    stack = [root]
    try:
        while stack:
            directory = stack.pop()
            with os.scandir(directory) as entries:
                for entry in entries:
                    path = Path(entry.path)
                    if _excluded(path, root, excludes):
                        continue
                    stat = entry.stat(follow_symlinks=False)
                    is_dir = entry.is_dir(follow_symlinks=False)
                    result[str(path)] = FileMeta((stat.st_dev, stat.st_ino), stat.st_size, stat.st_mtime_ns, is_dir)
                    if len(result) >= max_entries:
                        return result, "entry-limit"
                    if recursive and is_dir and not entry.is_symlink():
                        stack.append(path)
    except PermissionError:
        return result, "permission-denied"
    except OSError as error:
        return result, f"io-error:{error.errno}"
    return result, None


class FilesystemAdapter:
    def __init__(self):
        self.snapshots: dict[str, dict[str, FileMeta]] = {}
        self.last_poll: dict[str, float] = {}
        self.health: dict[str, str | None] = {}

    @staticmethod
    def key(listener: dict[str, Any]) -> str:
        config = listener.get("config", {})
        roots = sorted(str(Path(x).expanduser().resolve(strict=False)) for x in config.get("roots", []))
        return repr((roots, bool(config.get("recursive", False)), sorted(config.get("exclude", [])), int(config.get("maxEntries", 10000))))

    def poll(self, listeners: list[dict[str, Any]], now: float) -> list[Observation]:
        output: list[Observation] = []
        grouped: dict[str, list[dict[str, Any]]] = {}
        for listener in listeners:
            if listener["type"] in {"filesystem.watch", "trash.watch", "screenshot.watch"}:
                grouped.setdefault(self.key(listener), []).append(listener)
        for key, attached in grouped.items():
            config = attached[0].get("config", {})
            interval = float(config.get("pollSeconds", 1.0))
            if now - self.last_poll.get(key, 0) < interval:
                continue
            self.last_poll[key] = now
            current: dict[str, FileMeta] = {}
            degraded: str | None = None
            for raw_root in config.get("roots", []):
                root = Path(raw_root).expanduser().resolve(strict=False)
                snapshot, error = scan_root(root, bool(config.get("recursive", False)), list(config.get("exclude", [])), int(config.get("maxEntries", 10000)))
                current.update(snapshot)
                degraded = degraded or error
            previous = self.snapshots.get(key)
            self.snapshots[key] = current
            old_health = self.health.get(key)
            self.health[key] = degraded
            if degraded and degraded != old_health:
                for listener in attached:
                    output.append(Observation(
                        self._event_type(listener["type"], "degraded"), listener["id"], "filesystem",
                        {"code": degraded, "roots": config.get("roots", [])}, sensitivity="sensitive", origin="adapter.filesystem",
                    ))
            if previous is None:
                continue
            old_by_inode = {meta.inode: path for path, meta in previous.items()}
            new_by_inode = {meta.inode: path for path, meta in current.items()}
            moved_old = set()
            moved_new = set()
            for inode, old_path in old_by_inode.items():
                new_path = new_by_inode.get(inode)
                if new_path and new_path != old_path:
                    moved_old.add(old_path)
                    moved_new.add(new_path)
                    for listener in attached:
                        output.extend(self._map(listener, "moved", new_path, current[new_path], {"from": old_path}))
            for path, meta in current.items():
                if path in moved_new:
                    continue
                if path not in previous:
                    for listener in attached:
                        output.extend(self._map(listener, "created", path, meta, {}))
                elif meta.mtime_ns != previous[path].mtime_ns or meta.size != previous[path].size:
                    for listener in attached:
                        output.extend(self._map(listener, "modified", path, meta, {}))
            for path, meta in previous.items():
                if path not in current and path not in moved_old:
                    for listener in attached:
                        output.extend(self._map(listener, "removed", path, meta, {}))
        return output

    @staticmethod
    def _event_type(kind: str, operation: str) -> str:
        if kind == "trash.watch":
            return {"created": "trash.item.added", "removed": "trash.item.removed", "degraded": "trash.watch.degraded"}.get(operation, "trash.item.changed")
        if kind == "screenshot.watch":
            return "screenshot.detected" if operation == "created" else "screenshot.watch.degraded"
        return f"filesystem.{'watch' if operation == 'degraded' else 'entry'}.{operation}"

    def _map(self, listener: dict[str, Any], operation: str, path: str, meta: FileMeta, extra: dict[str, Any]) -> list[Observation]:
        kind = listener["type"]
        config = listener.get("config", {})
        if kind == "screenshot.watch":
            extensions = {str(x).lower() for x in config.get("extensions", [".png", ".jpg", ".jpeg", ".webp"])}
            if operation != "created" or Path(path).suffix.lower() not in extensions or meta.is_dir:
                return []
        if kind == "trash.watch" and operation not in {"created", "removed"}:
            return []
        data = {"path": path, "name": Path(path).name, "size": meta.size, "isDirectory": meta.is_dir, **extra}
        return [Observation(
            self._event_type(kind, operation),
            listener["id"],
            "filesystem",
            data,
            provenance="inferred" if kind == "screenshot.watch" else "observed",
            sensitivity="sensitive",
            origin="adapter.filesystem",
        )]


class MediaAdapter:
    def __init__(self):
        self.last_poll = 0.0
        self.players: dict[str, dict[str, str]] = {}
        self.degraded_emitted = False

    def poll(self, listeners: list[dict[str, Any]], now: float) -> list[Observation]:
        attached = [x for x in listeners if x["type"] == "media.mpris"]
        if not attached:
            return []
        interval = min(float(x.get("config", {}).get("pollSeconds", 1.0)) for x in attached)
        if now - self.last_poll < interval:
            return []
        self.last_poll = now
        playerctl = shutil.which("playerctl")
        if not playerctl:
            if self.degraded_emitted:
                return []
            self.degraded_emitted = True
            return [Observation("media.source.degraded", x["id"], "media", {"code": "playerctl-unavailable"}, origin="adapter.media") for x in attached]
        fmt = "{{playerName}}\\t{{status}}\\t{{title}}\\t{{artist}}\\t{{album}}\\t{{mpris:trackid}}"
        result = subprocess.run([playerctl, "-a", "metadata", "--format", fmt], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=2, check=False)
        current: dict[str, dict[str, str]] = {}
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                parts = line.split("\t")
                if len(parts) >= 6 and parts[0]:
                    current[parts[0]] = dict(zip(("player", "status", "title", "artist", "album", "trackId"), parts[:6]))
        output: list[Observation] = []
        for name, player in current.items():
            before = self.players.get(name)
            event_types = []
            if before is None:
                event_types.append("media.player.appeared")
            if before and before.get("status") != player.get("status"):
                event_types.append("media.playback.changed")
            if before and before.get("trackId") != player.get("trackId"):
                event_types.append("media.track.changed")
            for listener in attached:
                allowed = listener.get("config", {}).get("players", [])
                if allowed and name not in allowed:
                    continue
                for event_type in event_types:
                    output.append(Observation(event_type, listener["id"], "media", player, origin="adapter.media"))
        for name, player in self.players.items():
            if name not in current:
                for listener in attached:
                    output.append(Observation("media.player.disappeared", listener["id"], "media", player, origin="adapter.media"))
        self.players = current
        return output


class AdapterCoordinator:
    def __init__(self, state: dict[str, Any]):
        self.time = TimeAdapter(state)
        self.filesystem = FilesystemAdapter()
        self.media = MediaAdapter()

    def poll(self, listeners: list[dict[str, Any]], now: float) -> list[Observation]:
        return self.time.poll(listeners, now) + self.filesystem.poll(listeners, now) + self.media.poll(listeners, now)
