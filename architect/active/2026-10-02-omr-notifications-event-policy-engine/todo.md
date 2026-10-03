# Todo

## Decisions Before Activation

- [x] Confirm **OmR Notifications** and **Omarchy's Robust Notifications** as
  the display and expanded names.
- [x] Confirm the final non-reserved plugin ID:
  `uriak.omr-notifications`.
- [x] Reinspect the current Omarchy and Quickshell plugin contracts and pin the
  initial compatibility baseline.
- [x] Choose in-shell QML/JavaScript, a companion runtime, or a hybrid and
  record measured/prototyped rationale.
- [x] Choose the configuration syntax and schema validation implementation.
- [x] Choose the bounded journal/runtime-state backend and migration strategy.
- [x] Choose the initial UI surface: shell panel, setup flow, CLI, or a minimal
  combination.
- [x] Confirm the first vertical slice:
  `time.after` -> policy -> `notification.show` + `event.record`.
- [x] Set queue capacity, causal-depth ceiling, action concurrency, timeout,
  and output limits.
- [x] Set initial history/retention defaults and sensitive-field redaction.
- [x] Decide whether explicit ingress buffers events while OmR is unavailable
  or fails fast.
- [x] Define the exact acknowledgement thresholds for resource/privacy impact.

## Activation

- [x] User explicitly authorizes implementation of this package.
- [x] Move the package under `architect/active/`.
- [x] Update root assignment and handoff with the chosen implementation slice.
- [x] Record the initial file/module map and verification commands.

## Contracts

- [x] Define Listener schema and cross-reference rules.
- [x] Define Event envelope, type naming, sensitivity, and provenance rules.
- [x] Define Policy trigger, condition, control, and error semantics.
- [x] Define Action and Action Result contracts.
- [x] Define Impact Descriptor and acknowledgement fingerprint.
- [ ] Define typed health, diagnostic, and degradation codes.
- [x] Define configuration and stored-state versioning; add migrations when a
  second persisted version exists.

## Pure Engine

- [x] Implement immutable normalization and event sequencing.
- [x] Implement deterministic policy ordering.
- [x] Implement typed condition operators and safe field resolution.
- [x] Implement grouping, debounce, cooldown, and rate limits.
- [x] Implement terminal policies and action-error strategies.
- [ ] Implement correlation, causation, causal depth, origin filters, and action
  fingerprints.
- [x] Implement bounded queue and non-recursive visible overflow counters.

## Runtime and Persistence

- [x] Implement transactional configuration activation.
- [x] Implement last known-good recovery.
- [ ] Implement adapter registry, sharing keys, and lifecycle reconciliation.
- [x] Implement global pause and bounded shutdown.
- [x] Implement bounded runtime state and journal stores.
- [ ] Implement retention, deletion, migration, and payload cleanup.

## Adapters

- [x] Implement `time.at`, `time.after`, and interval-based `time.schedule` semantics.
- [x] Implement schedule reconciliation and missed-event policies.
- [ ] Implement shared MPRIS observation and metadata stabilization.
- [x] Implement allowlisted Omarchy hook/explicit ingress.
- [x] Implement consolidated scoped filesystem polling.
- [ ] Implement move correlation, recursive root updates, watch accounting, and
  overflow/degradation behavior.
- [x] Implement initial Trash normalization over explicitly configured roots.
- [ ] Implement explicit and observed screenshot sources with deduplication.

## Actions

- [x] Implement Companion `notification.show` and owned logical replacement.
- [x] Implement owned `notification.dismiss`.
- [x] Implement `osd.show`.
- [x] Implement bounded `sound.play`.
- [x] Implement literal, time-bounded `exec.argv`.
- [x] Implement idempotent `listener.enable` and `listener.disable`.
- [x] Implement sensitivity-aware `event.record`.

## UI and Diagnostics

- [x] Implement JSON/CLI listener configuration and lifecycle status.
- [x] Implement impact preflight and fingerprint acknowledgement.
- [x] Implement JSON policy configuration and synthetic fixture testing.
- [x] Implement event/action-result explanation subject to retention.
- [x] Implement global pause, degradation events, and safe action failures.
- [x] Keep backend terms in diagnostics rather than the main panel workflow.

## Verification

- [x] Validate configuration/contracts against fixtures; no migration is needed
  until a second persisted version exists.
- [x] Test deterministic policy order and every control with a fake clock.
- [ ] Test action error strategies and bounded concurrency.
- [ ] Test causal loops from notifications, files, media, and listener state.
- [x] Test invalid configuration and last known-good recovery.
- [ ] Test adapter sharing, reference release, reconnect, and degradation.
- [ ] Test time restart, suspend/resume, timezone, and missed behavior.
- [ ] Test MPRIS player churn and partial metadata.
- [ ] Test filesystem recursion, exclusions, rename cookies, root loss, watch
  exhaustion, and overflow.
- [ ] Test Trash metadata variants and screenshot provenance/deduplication.
- [ ] Measure idle/burst PSS, CPU, wakeups, watch count, storage growth, and
  shutdown release before publishing resource claims.
- [x] Run source-tree manifest/JSON, Python compile, CLI, and dry-run smoke checks
  before any installed-plugin test.
- [ ] Run installed Companion-mode tests only after separate authorization.
- [ ] Verify uninstall/disable leaves no active watchers, timers, hooks, or
  stale shell references.

## Deferred

- [ ] Create a separate Provider-mode Architect package after Companion mode is
  implemented, verified, and measured.
