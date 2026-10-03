# OmR Notifications

**OmR Notifications** (Omarchy's Robust Notifications) is a local event-policy
runtime for Omarchy. It observes explicitly enabled sources, normalizes events,
evaluates deterministic policies, and dispatches bounded actions.

This repository contains a source-complete Companion-mode v0.1. Its reviewed
snapshot is installed and enabled in the local Omarchy desktop; the source,
installed snapshot, live configuration, and running process remain distinct.

```text
Source Adapter -> Listener -> Immutable Event -> Policy -> Typed Actions
```

## What is implemented

- An Omarchy manifest-schema-1 plugin (`uriak.omr-notifications`) with a
  keep-loaded service and a small bar status/pause/reload panel.
- A dependency-free Python 3.11+ Companion runtime and CLI.
- Versioned Listener, Event, Policy, Action, Action Result, Impact, and
  Configuration contracts under `schemas/`.
- Deterministic policy order (priority descending, then ID), typed conditions,
  grouping, debounce, cooldown, rate limiting, terminal policies, and action
  error strategies.
- Stable event sequencing; separate occurrence/observation times; provenance,
  sensitivity, origin, correlation, causation, and bounded causal depth.
- Transactional configuration reload with last-known-good recovery.
- Bounded event queue, command output, ingress size, action duration, journal
  count, and journal bytes.
- `time.after`, `time.at`, interval-based `time.schedule`, strict local ingress,
  allowlisted Omarchy hook events, shared polling for scoped filesystems,
  FreeDesktop Trash-compatible roots, screenshot-directory inference, and an
  optional `playerctl` MPRIS adapter.
- Companion actions for notifications, owned notification dismissal, Omarchy
  OSD, sound, literal argv execution, listener state, and bounded recording.
- Notification actions prefer the FreeDesktop service and fall back to
  Omacale's scoped toast IPC when that desktop service has no owner.
- Machine-readable resource/privacy preflight with acknowledgement
  fingerprints.

OmR does not own `org.freedesktop.Notifications`, intercept unrelated desktop
notifications, use shell command evaluation, read watched-file contents, or
perform global filesystem/process surveillance. Provider mode remains deferred.

## Try it from the source tree

No installation is required for source-level use:

```bash
python3 bin/omr-notifications config validate examples/config.example.json
python3 bin/omr-notifications preflight examples/config.example.json
python3 bin/omr-notifications test-policy \
  examples/fixtures/time-after.json --config examples/config.example.json
PYTHONPATH=src python3 -m unittest discover -v
```

To create the default empty user configuration (this is an explicit write to
your XDG config directory):

```bash
python3 bin/omr-notifications config init
```

The runtime commands are:

```bash
python3 bin/omr-notifications run
python3 bin/omr-notifications status
python3 bin/omr-notifications pause
python3 bin/omr-notifications resume
python3 bin/omr-notifications reload
python3 bin/omr-notifications journal --count 20
python3 bin/omr-notifications shutdown
```

Submit to an enabled `explicit.ingress` listener:

```bash
python3 bin/omr-notifications emit build.completed \
  --listener local-input \
  --data '{"project":"example","result":"success"}'
```

Ingress fails fast when the runtime socket is unavailable; events are not
silently buffered.

## Configuration

The default configuration path is
`${XDG_CONFIG_HOME:-~/.config}/omr-notifications/config.json`. The complete
example is [examples/config.example.json](examples/config.example.json).

```json
{
  "schemaVersion": 1,
  "revision": 1,
  "listeners": [
    {
      "id": "local-input",
      "type": "explicit.ingress",
      "enabled": true,
      "config": { "eventTypes": ["build.completed"] }
    }
  ],
  "policies": [
    {
      "id": "show-completed-build",
      "enabled": true,
      "priority": 100,
      "trigger": {
        "types": ["build.completed"],
        "listenerIds": ["local-input"]
      },
      "conditions": [
        { "field": "data.result", "operator": "eq", "value": "success" }
      ],
      "controls": { "cooldownSeconds": 5 },
      "actions": [
        {
          "type": "notification.show",
          "config": {
            "title": "Build complete",
            "body": "${event.data.project} succeeded",
            "replaceKey": "build-result"
          }
        },
        { "type": "event.record", "config": {} }
      ],
      "terminal": false,
      "errorStrategy": "continue"
    }
  ],
  "impactAcknowledgements": []
}
```

Run `preflight` before enabling watched paths. Sensitive or recursive watch
scopes produce a fingerprint. Add only reviewed fingerprints to
`impactAcknowledgements`; command policies require the literal acknowledgement
`"exec.argv"`. Until acknowledged, those listeners or command policies remain
inactive.

Templates use allowlisted event paths in the form `${event.data.name}`. They do
not evaluate expressions. `exec.argv` passes each rendered entry as one literal
argument with `shell=False`; the child receives the current environment, no
stdin, an optional resolved working directory, a timeout, and truncated output.

## Runtime data

OmR keeps mutable data out of the plugin source:

| Purpose | Default path |
| --- | --- |
| Configuration | `${XDG_CONFIG_HOME:-~/.config}/omr-notifications/` |
| Last known-good config, schedule state, journal | `${XDG_STATE_HOME:-~/.local/state}/omr-notifications/` |
| Regeneratable cache | `${XDG_CACHE_HOME:-~/.cache}/omr-notifications/` |
| Same-user socket and live status | `${XDG_RUNTIME_DIR}/omr-notifications/` |

State and runtime files are written with user-only permissions. Sensitive
events are not retained unless `retention.sensitive` is explicitly enabled.

## Omarchy integration

The source targets Omarchy `4.0.4-1` and plugin manifest schema 1. When the
plugin is enabled through Omarchy's normal plugin flow, `Service.qml` owns the
Companion process for the shell lifetime; it does not install a systemd unit.
`Panel.qml` exposes status, counters, pause/resume, and reload controls.
Socket ownership is atomic: if Omarchy and a replacement bar both instantiate
the service, only one Companion runs and the other instance reads shared status.

The current source snapshot is installed at
`~/.config/omarchy/plugins/uriak.omr-notifications`, enabled immediately before
`omarchy.power` in the right bar section, and hosted by the running Omarchy
Shell. No packages, hooks, user services, or packaged files under
`/usr/share/omarchy` were changed.

## Current limitations

- `time.schedule` is a durable interval schedule, not a cron-expression parser.
- Media support uses `playerctl` when already available and reports a degraded
  source when it is absent. It is polling-based in v0.1.
- Filesystem observation is consolidated polling rather than inotify. Moves
  are correlated by device/inode; overflows and missing/denied roots become
  degradation events.
- Screenshot directory events are correctly labeled `inferred`; authoritative
  screenshot and Omarchy-hook events should use explicit ingress.
- The status panel is intentionally minimal; configuration and fixture testing
  are CLI/JSON workflows in v0.1.
- The live QML surface is intentionally limited to runtime status and controls;
  policy authoring remains a reviewed JSON/CLI workflow.

See [AGENTS.md](AGENTS.md) and the active Architect record under
`architect/active/2026-10-02-omr-notifications-event-policy-engine/` for the
full safety and design contract.
