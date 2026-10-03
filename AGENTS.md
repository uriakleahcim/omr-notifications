# Agent guide: OmR Notifications

This file contains durable repository rules. Put task-specific plans,
decisions, progress, and verification evidence in `architect/`.

## Getting Oriented

1. Read `architect/ASSIGNMENT.md` for the current execution state.
2. Read `architect/README.md` for lifecycle rules and
   `architect/PROJECT.md` for the project adapter.
3. Read the primary pending or active Architect entry before changing files.
4. Inspect the current branch, tree, and Git status. Preserve unrelated or
   concurrent work.
5. For Omarchy behavior, inspect the current installed/source tree rather than
   assuming an older plugin contract is still authoritative.

## Current Phase

- Companion-mode v0.1 source is implemented.
- The current package is active at
  `architect/active/2026-10-02-omr-notifications-event-policy-engine/`.
- The source uses a dependency-free Python runtime/CLI hosted by a small QML
  service and bar widget.
- The reviewed source snapshot is installed and enabled as
  `uriak.omr-notifications`; the running Companion is live and verified.
- Further hook installation, systemd units, package changes, Provider mode, or
  broader host integration remain unauthorized unless the user asks for them
  separately.

## Product Vocabulary

- A **source adapter** is the shared implementation that connects to one event
  provider. Do not create one MPRIS connection, watcher process, or scheduler
  for every listener.
- A **listener** is user configuration that scopes an adapter and enables or
  disables event production.
- An **event** is an immutable, versioned fact or observation. Preserve
  `occurredAt` separately from `observedAt`; do not invent the former when a
  source does not provide it.
- A **policy** contains a trigger, conditions, execution controls, and ordered
  actions. Trigger matching is not the same as source subscription.
- An **action** is a bounded side effect. Prefer typed actions and literal argv
  over generic command strings.

## Architectural Invariants

- Keep adapters, listener configuration, normalized events, policy evaluation,
  and action dispatch behind separate interfaces.
- Keep infrastructure terms such as systemd, MPRIS, inotify, and Quickshell out
  of the normalized policy model unless exposed as source metadata.
- Assign deterministic event sequence numbers and deterministic policy order.
- Preserve provenance as `explicit`, `observed`, or `inferred`. Confidence is
  meaningful primarily for inferred events.
- Carry `correlationId`, `causationId`, origin, and causal depth through action
  chains. Prevent notification, filesystem, media, and listener-state feedback
  loops by default.
- Bound queues, retries, history, media payloads, filesystem scope, and
  concurrent actions. Overflow or degradation must become visible state.
- Parse and validate a complete configuration before swapping it into the live
  runtime. Keep the last known-good configuration after an invalid edit.
- Do not promise exact per-listener RAM while code shares the
  `omarchy-shell` process. Report measurable process deltas, watch counts,
  polling intervals, child processes, retention, and data sensitivity.
- Treat implementation placement as replaceable: domain contracts must not
  depend on whether a future component runs in QML, a companion process, or a
  transient helper.

## Omarchy Integration Boundaries

- Never modify `/usr/share/omarchy/`; it is packaged, read-only reference
  material and updates may replace it.
- User-owned plugin code belongs under the normal Omarchy plugin flow. Source
  checkout, installed plugin, and running `omarchy-shell` state are distinct.
- Third-party plugin IDs must not use the reserved `omarchy.*` namespace.
- Companion mode is the default initial architecture. It emits allowed events
  through the existing notification service and does not filter unrelated
  application notifications.
- Provider mode cannot safely coexist with the stock notification daemon. It
  requires a separately activated package, transactional takeover, health
  verification, and rollback.
- Use existing Omarchy hooks where they provide an exact event. Do not patch
  packaged commands to manufacture hooks.
- Host changes such as enabling a plugin, installing hook scripts, creating
  systemd units, editing shell configuration, or starting watchers require
  explicit authorization and separate live verification.

## Safety, Privacy, and Execution

- Default to minimum local metadata and explicit watch scopes.
- Treat paths, filenames, notification bodies, media metadata, clipboard data,
  and action arguments as potentially sensitive.
- Do not persist file contents or clipboard contents in the initial scope.
- Do not introduce global filesystem monitoring, privileged audit rules,
  fanotify, eBPF, or broad process observation without a new approved package.
- Keep `exec.argv` as a literal argument array and reject malformed values.
  `exec.shell` is out of scope unless separately designed, warned, and approved.
- Never store runtime state in the source checkout. Use planned XDG config,
  state, cache, and runtime locations after their contracts are approved.
- Do not commit generated runtime data, histories, images, logs, secrets,
  exports, or local activation state.

## Verification Expectations

- Test normalized contracts and policy behavior with fixtures before live
  desktop integration.
- Test policy ordering, debounce, cooldown, terminal behavior, action failures,
  causality depth, and loop suppression deterministically.
- Test adapter startup, shutdown, degradation, reconnection, overflow, and
  configuration reload independently.
- For filesystem behavior, test rename cookies, newly created directories,
  excluded paths, watch-limit failure, root disappearance, and queue overflow.
- For time behavior, test timezone, suspend/resume, missed-event policies, and
  restart recovery.
- Separate source tests, fixture tests, live read-only observation, installed
  plugin tests, and provider takeover tests in reports. One does not prove the
  others.
- Measure resource use before publishing numeric claims.

## Source Verification

```bash
PYTHONPATH=src python3 -m unittest discover -v
python3 -m compileall -q src tests
python3 bin/omr-notifications config validate examples/config.example.json
python3 bin/omr-notifications preflight examples/config.example.json
git diff --check
```
