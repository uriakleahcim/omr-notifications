from __future__ import annotations

CONFIG_VERSION = 1
EVENT_VERSION = 1
ACTION_RESULT_VERSION = 1
IMPACT_VERSION = 1

DEFAULT_LIMITS = {
    "queueCapacity": 256,
    "causalDepth": 8,
    "actionConcurrency": 4,
    "actionTimeoutSeconds": 10.0,
    "actionOutputBytes": 16 * 1024,
    "ingressBytes": 64 * 1024,
    "journalRecords": 2_000,
    "journalBytes": 8 * 1024 * 1024,
}

LISTENER_TYPES = {
    "time.after",
    "time.at",
    "time.schedule",
    "media.mpris",
    "omarchy.hook",
    "filesystem.watch",
    "trash.watch",
    "screenshot.watch",
    "explicit.ingress",
}

ACTION_TYPES = {
    "notification.show",
    "notification.dismiss",
    "osd.show",
    "sound.play",
    "exec.argv",
    "listener.enable",
    "listener.disable",
    "event.record",
}

PROVENANCE = {"explicit", "observed", "inferred"}
SENSITIVITY = {"public", "local", "sensitive"}
ERROR_STRATEGIES = {"continue", "stop-policy", "stop-event"}
