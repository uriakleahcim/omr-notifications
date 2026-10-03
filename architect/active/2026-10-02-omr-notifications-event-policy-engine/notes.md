# Notes and Decision Ledger

## Settled Direction

- Working display name: **OmR Notifications**.
- Expanded working name: **Omarchy's Robust Notifications**.
- Public description: **Omarchy's event-driven notification and automation
  policy engine**.
- Prefer **event-policy runtime** or **event router** over **desktop event bus**
  until a stable external publish/subscribe contract exists.
- Public vocabulary: Listener, Event, Policy, Action.
- Internal shared integration vocabulary: Source Adapter.
- Initial mode: Companion.
- Deferred mode: Provider.
- Provider mode must be a separately activated Architect package.

## Activation Decisions (2026-10-03)

- The user explicitly re-authorized implementation after the scheduled run did
  not survive a host reboot.
- Plugin ID: `uriak.omr-notifications`.
- Compatibility baseline: Omarchy `4.0.4-1`, plugin manifest schema 1.
- Runtime: hybrid. A small QML service/bar widget owns a dependency-free Python
  Companion process. Domain contracts remain Python-only and independent of
  QML object lifetimes.
- Configuration: versioned JSON with strict manual validation and complete
  cross-reference checks before activation.
- State: atomic JSON snapshots plus a bounded JSONL journal under XDG state.
  No database or third-party dependency is required for v1.
- UI: a minimal Omarchy bar status panel plus a complete CLI for validation,
  preflight, status, event submission, pause, reload, and fixture evaluation.
- First vertical slice: normalized ingress and time events through deterministic
  policies to `notification.show` and `event.record`; other bounded actions and
  polling adapters build on the same contracts.
- Bounds: queue 256, causal depth 8, action concurrency 4, default action
  timeout 10 seconds, action output 16 KiB, journal 2,000 records / 8 MiB.
- Explicit ingress fails fast when the local runtime socket is unavailable.
- Resource acknowledgement is required for sensitive paths, recursive watches,
  polling below one second, or command actions; acknowledgements are bound to a
  deterministic impact fingerprint.

## Semantic Decisions

- A source adapter owns a shared integration; listener instances scope it.
- Trigger matching belongs inside a policy and does not create subscriptions.
- `occurredAt` and `observedAt` are distinct. Unknown occurrence time remains
  null.
- Provenance values are `explicit`, `observed`, and `inferred`.
- Confidence is optional and primarily applies to inferred events.
- Filesystem namespace removal is `filesystem.entry.removed`, not proof that
  the underlying file data was destroyed.
- Time event types are `time.at`, `time.after`, and `time.schedule`.
- Notification replacement is expressed through a stable `replaceKey` on
  `notification.show`, not by exposing transient daemon IDs to policies.
- No match means no action. `event.ignore` is not needed as a normal action.
- A terminal policy can intentionally stop later matching policies.
- `exec.argv` is supported in principle; `exec.shell` is excluded from the
  initial package.

## Reliability Decisions

- Every event receives a stable ID, local sequence, correlation ID, origin,
  and causal depth.
- Every action result is recorded as success, failure, skipped, suppressed, or
  timed out.
- Configuration updates are all-or-nothing and retain a last known-good copy.
- Queue overflow, watch overflow, source disconnect, and permission failure are
  observable degraded states.
- Adapter instances are reference-counted or centrally reconciled so equivalent
  listeners share one underlying subscription.

## Resource Decisions

- Resource impact is a machine-readable adapter report, not free-form warning
  text.
- Preflight distinguishes resident work, polling, watch descriptors, child
  processes, wakeups, privileges, captured data classes, and retention.
- Numeric memory claims require controlled measurements. Shared QML memory is
  reported as process-level deltas, not exact listener ownership.
- One consolidated filesystem watcher is preferred over one process per
  listener.
- Durable time schedules are preferred over one in-memory QML timer per event.

## Local Omarchy Snapshot Used for Planning

The local installed Omarchy snapshot inspected on 2026-10-02 was version
4.0.4-1. It exposed:

- first-party `omarchy.notifications` and `omarchy.media` shell services;
- third-party service plugin loading from user-owned plugin directories;
- plugin enable/disable through shell configuration and IPC;
- documented hooks including post-boot, post-update, theme-set, font-set, and
  battery-low;
- reminders backed by transient user-level systemd timers;
- screenshot commands that notify for some flows but no dedicated documented
  screenshot hook;
- current plugin activation without a standard manifest-level resource-warning
  contract.

These are planning observations, not permanent compatibility guarantees. Recheck
the current Omarchy tree before implementation.

## Implementation Result (2026-10-03)

- `manifest.json`, `Service.qml`, and `Panel.qml` implement the source plugin
  boundary without installing or enabling it.
- `src/omr_notifications/` implements configuration, immutable events,
  deterministic policies, adapters, typed actions, bounded persistence, and a
  same-user Unix-socket control/ingress surface.
- `bin/omr-notifications` exposes configuration validation/init, preflight,
  status, pause/resume/reload/shutdown, strict event submission, journal tail,
  schema display, and fixture policy evaluation.
- `schemas/` carries versioned JSON contract documents; `examples/` carries a
  safe source configuration and event fixture.
- Filesystem, Trash, and screenshot listeners share polling snapshots by
  subscription key. This is intentionally described as polling, not inotify.
- Media polling uses `playerctl` only when already present; absence emits a
  typed degradation event and does not trigger package installation.
- The engine is sequential, so action concurrency is bounded to one in v0.1
  even though the configuration ceiling reserves the future parallel limit.

## Verification Evidence (2026-10-03)

- 30 Python unit/fixture tests passed.
- Python compilation, JSON parsing, config validation, preflight, and
  `git diff --check` passed.
- An isolated dry-run process under `/tmp` verified the Unix socket, status,
  pause, resume, forced reload, allowlisted hook ingress, event sequencing,
  bounded recording, and graceful shutdown.
- No notification/OSD was dispatched during the smoke test (`--dry-run`).
- QML was checked against the local Omarchy `4.0.4-1` source contract and then
  installed and loaded into the running shell with explicit user authorization.

## First Live Launch (2026-10-03)

- Installed a source snapshot as `~/.config/omarchy/plugins/uriak.omr-notifications`
  and the reviewed example configuration under `~/.config/omr-notifications/`.
- Enabled the widget immediately before `omarchy.power` in the right bar
  section; the Companion process and same-user socket started successfully.
- Live loading exposed a missing `Quickshell.Io` import in `Panel.qml`; fixed in
  source and the installed snapshot.
- The desktop had no `org.freedesktop.Notifications` owner because both stock
  and cloned providers were disabled. `notification.show` now preserves the
  standard `notify-send` path and falls back to the active Omacale toast IPC
  when D-Bus reports `ServiceUnknown`.
- Omarchy's generic service host and Omacale's compatibility host can race to
  instantiate the same service. Runtime socket ownership is now atomic; a
  duplicate exits with code 75 and remains a status-only QML instance instead
  of unlinking and stealing the live socket.
- After the final shell restart, exactly one Companion process remained, the
  panel IPC returned `Listening`, runtime files were mode `0600`, and a real
  `notification.show` action succeeded through the Omacale toast fallback.

## Initial Publish and Integration Review (2026-10-03)

- Added workspace-level guidance that makes this plugin the reference for
  creating and suppressing notification events while preserving the source,
  installed snapshot, live configuration, and running-process distinction.
- Reviewed Omarchy Keymap's literal-only `push_notification()` parser, shared
  `notification_argv()` builder, safely quoted keyboard compilation, and direct
  foreground-event argv execution. Focused core and event-runtime tests passed
  30 tests; no Keymap files or live mappings were changed.
- Prepared the complete source tree for its initial commit and canonical GitHub
  remote at `https://github.com/uriakleahcim/omr-notifications`.
- Deferred implementation of a Codex CLI response-complete event until its
  supported completion-hook surface and desired notification payload are
  discussed. The preferred design is narrow `explicit.ingress`, not process or
  terminal scraping.

## Rich Notifications and Codex Bridge (2026-10-03)

- Extended `notification.show` to the reviewed Keymap capability set: glyph,
  urgency, timeout, icon, confined image, app name, logical replacement, and
  optional literal click argv. Click commands share the fail-closed
  `"exec.argv"` acknowledgement boundary.
- Added the `codex-notify` adapter for Codex's supported
  `agent-turn-complete` notifier payload. It forwards only project/cwd and
  thread/turn identifiers; prompt and assistant-response text are discarded.
- Added the closest available Devicon AI SVG through Iconify
  (`devicon:aiassistant`; `devicon:codex` is not published) and a
  symbolic `smart_toy` icon for the reduced Omacale fallback path.
