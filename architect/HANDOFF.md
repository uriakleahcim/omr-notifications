# Assignment Handoff

## Current State

- assignmentStatus: active
- lastUpdatedAt: 2026-10-03T14:59:00-04:00
- objectiveId: `2026-10-02-omr-notifications-event-policy-engine`
- primaryEntry:
  `architect/active/2026-10-02-omr-notifications-event-policy-engine`
- branch: `main`
- commit: v0.2 implementation; see Git history
- remote: `https://github.com/uriakleahcim/omr-notifications`

The Companion-mode v0.2 source is implemented and its reviewed snapshot is
installed and enabled as `uriak.omr-notifications`. Omarchy Shell owns one live
Companion process; no user service or additional hook was installed.

## Implemented Architecture

```text
QML Service + status panel
          |
          v
Python Companion runtime / CLI
  -> shared adapters
  -> immutable normalized events
  -> bounded queue
  -> deterministic policy engine
  -> typed action dispatcher
  -> bounded XDG state/journal
```

The plugin ID is `uriak.omr-notifications`. `Service.qml` owns one Python child
for the shell lifetime; no systemd unit is required. The Python core uses only
the standard library. Optional media polling uses an already-installed
`playerctl` and becomes visibly degraded when it is unavailable.

## Important Decisions

- Companion mode only; never own `org.freedesktop.Notifications`.
- Python owns domain contracts and mutable state; QML owns shell lifecycle and
  status controls.
- JSON configuration is validated completely before activation. Invalid edits
  retain the prior live snapshot and last-known-good state.
- Mutable data uses XDG config/state/cache/runtime paths, never source files.
- Sensitive/recursive watched paths require a configuration-bound SHA-256
  impact fingerprint. `exec.argv` policies require `"exec.argv"`
  acknowledgement and remain inactive otherwise.
- Commands are literal argv with `shell=False`, bounded timeout/output, no
  stdin, current environment, and optional resolved working directory.
- Filesystem/screenshot/Trash observation is consolidated polling in v0.1;
  it never reads file contents or follows directory symlinks recursively.
- Provider mode, native inotify/MPRIS subscriptions, cron syntax, and a visual
  configuration editor are follow-ups, not hidden partial implementations.
- Rich notification actions use `omarchy notification send` for glyph, icon,
  image, timeout, app name, replacement, and click argv. Relative images stay
  inside plugin `assets/`; click argv requires `"exec.argv"` acknowledgement.
- Codex's supported user-level notifier maps only `agent-turn-complete` into an
  explicit ingress event. Prompt and response bodies are deliberately omitted.

## Verification Performed

- `PYTHONPATH=src python3 -m unittest discover -v`: 30 tests passed.
- `python3 -m compileall -q src tests`: passed.
- Every repository JSON document parsed with `python3 -m json.tool`.
- `git diff --check`: passed.
- Isolated dry-run runtime smoke in `/tmp` passed:
  - created the same-user Unix socket and live status;
  - fired and recorded `time.after` without dispatching a notification;
  - exercised status, pause, resume, reload, allowlisted hook ingress, and
    graceful shutdown;
  - confirmed event sequencing and status counters.
- The source manifest was checked against the locally installed Omarchy
  `4.0.4-1` manifest-schema-1 contract.

- Live QML IPC reports `Listening`; one Companion owns the user-only socket,
  two configured listeners are active, and the status reports no last error.
- A real `notification.show` action succeeded through the Omacale toast
  fallback because no FreeDesktop notification provider is currently active.
- The v0.2 test suite passes 40 tests. A synthetic official-shape Codex payload
  was accepted live, produced the popup, and left `failedActions` at zero.
- Live status showed configuration revision 2, three active listeners, two
  active policies, and exactly one Companion process. The Codex and OmR config
  files remain mode `0600`.

## Known Limitations

- Interval schedules are durable, but cron/calendar expressions are absent.
- MPRIS support is polling-based through optional `playerctl`.
- Filesystem scope uses polling rather than inotify and therefore reports
  configured roots/entry caps instead of kernel watch counts.
- Screenshot directory matches are inferred. Explicit cooperating producers
  should submit authoritative events through local ingress.
- The QML panel handles status/pause/reload; listener and policy authoring is a
  CLI/JSON workflow.
- Resource numbers have not been measured, so no RAM/CPU claims are published.

## Preservation and Boundaries

The original scaffold was preserved and activated in place. The user-authorized
live launch created the installed snapshot and initial XDG configuration, and
updated the user-owned shell layout. No packaged Omarchy file, hook, timer,
service, package, remote, or Git history was changed. Do not conflate the source
tree, installed snapshot, and running shell instance.

## Safest Next Step

Observe one natural callback from a newly started Codex CLI process. For later
automation, retain the same payload-minimization and preflight boundaries.

## Integration Review (2026-10-03)

- Workspace-level agent guidance now points notification event creation and
  suppression work to this repository, its Listener -> Event -> Policy ->
  Action model, schemas, validation, and preflight boundary.
- Reviewed Omarchy Keymap's existing `push_notification()` implementation.
  `keymap/model.py` permits only literal validated arguments;
  `keymap/backend.py` generates one logical `omarchy notification send` argv;
  keyboard compilation applies `shlex.join`, while `keymap/action_runner.py`
  passes that argv directly to `Popen` for foreground native-event rules.
- Keymap image paths are confined to profile `assets/` when relative and click
  commands stay an argv list. Focused core/event-runtime verification passed
  30 tests. No Keymap source, profile, installed copy, binding, or live
  notification was changed.
- The supported Codex `notify` command is configured in user-level
  `~/.codex/config.toml`; official documentation says it currently receives
  `agent-turn-complete`. The OmR adapter is best-effort so a missing runtime can
  never turn a completed Codex response into a CLI failure.
