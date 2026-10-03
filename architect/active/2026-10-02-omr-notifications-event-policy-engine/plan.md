# Implementation Plan

This plan is inactive until the Architect entry is explicitly moved to
`architect/active/`. Each phase must leave the repository in a verifiable state.

## Phase 0: Activate and Freeze Decisions

- Confirm project/display name and final plugin ID.
- Pin the supported Omarchy and Quickshell baseline after reinspection.
- Decide runtime placement and whether a companion component is justified.
- Choose configuration syntax and storage backend.
- Set initial resource, queue, retention, and causal-depth defaults.
- Choose the first UI surface and first vertical slice.
- Update `architect/PROJECT.md`, `ASSIGNMENT.md`, and `HANDOFF.md`.

Exit gate: active record contains decisions, exact file scope, commands, and
verification baseline. No host activation is necessary for this phase.

## Phase 1: Contracts and Fixture Harness

- Create versioned schemas/models for Listener, Event, Policy, Action, Action
  Result, and Impact Descriptor.
- Add structural and semantic validation.
- Add fixture serialization and redaction utilities.
- Define typed error/diagnostic codes.
- Create representative fixtures for time, media, hooks, filesystem, Trash,
  screenshot, and causal chains.

Exit gate: malformed and unsupported versions fail deterministically; valid
fixtures round-trip without retaining undeclared raw fields.

## Phase 2: Pure Core Runtime

- Implement event normalization and local sequencing.
- Implement deterministic trigger/condition evaluation.
- Implement grouping, debounce, cooldown, rate limits, and terminal behavior
  with an injectable clock.
- Implement action request planning without I/O.
- Implement correlation, causation, causal depth, origin filtering, and action
  fingerprint guards.
- Implement bounded queue behavior and diagnostic counters.

Exit gate: pure tests cover ordering, timing controls, error strategies,
overflow, and self-trigger loops without a live desktop.

## Phase 3: Configuration and Runtime Coordination

- Implement configuration loading, migration, validation, and last known-good
  retention.
- Implement adapter registry and shared-runtime reconciliation.
- Implement adapter lifecycle/health states.
- Implement global pause and bounded shutdown.
- Implement impact descriptor aggregation and acknowledgement fingerprints.

Exit gate: invalid live reload leaves the previous revision active; equivalent
listeners share one adapter instance; disabling the final listener releases it.

## Phase 4: First Vertical Slice

Recommended first slice: `time.after` -> policy -> `notification.show` plus
`event.record`, because it proves the entire path without filesystem scale or
MPRIS stabilization complexity.

- Implement the selected schedule backend behind the time adapter.
- Implement Companion notification dispatch.
- Implement a minimal bounded journal/status surface.
- Verify restart and missed-event semantics with fixtures and controlled tests.

Exit gate: one explicitly configured reminder survives the declared lifecycle,
fires once, records an explainable result, and can be removed without residue.

## Phase 5: Media and Omarchy Hooks

- Add shared MPRIS observation and stable player identities.
- Add metadata stabilization and track-signature deduplication.
- Add validated explicit ingress.
- Add user-owned hook shims only in source first; installation remains a
  separately authorized operation.
- Add OSD and sound actions if included in the activated slice.

Exit gate: fixtures and source tests prove normalized media/hook events and
bounded action behavior; live observation is reported separately.

## Phase 6: Filesystem, Trash, and Screenshot

- Implement the consolidated watcher controller.
- Add watch accounting, recursion, exclusions, move correlation, and overflow.
- Add Trash metadata normalization.
- Add explicit screenshot ingress and observed-directory fallback.
- Deduplicate authoritative and observed screenshot events.
- Add path privacy/redaction tests.

Exit gate: scoped fixture/integration tests cover movement versus removal,
dynamic subdirectories, watch exhaustion, overflow, and clean resource release.

## Phase 7: UI and Resource Preflight

- Implement listener list/editor, policy editor, synthetic event test, health,
  and diagnostics surfaces according to the selected UI boundary.
- Present impact descriptors and current system limits.
- Require acknowledgement for material impact changes.
- Add resource measurement scenarios and record methodology.

Exit gate: a user can understand and safely enable/disable every supported
listener without editing raw runtime internals.

## Phase 8: Packaging and Companion Live Verification

- Validate the plugin manifest and source package.
- Verify source checkout separately from installed plugin state.
- Test enable, disable, update/reload, failure recovery, and uninstall cleanup.
- Verify no packaged Omarchy file is modified.
- Measure idle/burst resource behavior and shutdown release.

Exit gate: Companion mode meets acceptance criteria and can be removed without
leaving active watchers, timers, hooks, or stale configuration references.

## Separate Future Package: Provider Mode

Do not fold this into the preceding phases. Create a new pending Architect
entry covering stock notification parity, D-Bus ownership, pass-through,
replacement IDs, actions/replies, DND/history/UI, pre-activation warnings,
transactional takeover, and rollback.
