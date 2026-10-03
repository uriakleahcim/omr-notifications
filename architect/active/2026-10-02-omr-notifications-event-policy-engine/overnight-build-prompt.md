# Scheduled OmR Notifications Companion Build

Work autonomously in `/home/uriak/Work/AppSource/com.github/omr-notifications`.

The user explicitly authorizes implementation of the pending **Companion-mode**
OmR Notifications package during this scheduled run. Create a goal for the
complete objective and continue until it is achieved or the scheduled process
is terminated. Do not stop merely because an intermediate milestone passes.

## Start by orienting

1. Read `AGENTS.md`, `architect/ASSIGNMENT.md`, `architect/PROJECT.md`, and the
   complete pending record under
   `architect/active/2026-10-02-omr-notifications-event-policy-engine/`.
2. Inspect the branch, Git status, current tree, installed Omarchy reference
   behavior, and relevant plugin validation/runtime contracts.
3. Preserve all existing scaffold work.
4. Activate the pending Architect record before creating implementation files;
   update `ASSIGNMENT.md` and `HANDOFF.md` accordingly.

## Objective

Implement the strongest coherent, tested Companion-mode OmR Notifications v1
that can be completed safely in this run. Preserve the documented boundaries:

```text
Source Adapter -> Configured Listener -> Normalized Event
               -> Policy -> Action Dispatcher -> Results
```

Prioritize, in order:

1. A valid third-party Omarchy service plugin structure and manifest.
2. Versioned Listener, Event, Policy, Action, Action Result, and Impact
   Descriptor contracts with validation.
3. Deterministic policy evaluation, including priority, typed conditions,
   grouping, debounce, cooldown, rate limiting, terminal behavior, and action
   error strategies.
4. Event sequencing, provenance, sensitivity, correlation, causation, causal
   depth, origin filtering, and feedback-loop prevention.
5. Transactional configuration loading with last known-good recovery and
   bounded queues/state.
6. Time events (`time.at`, `time.after`, and a defensible initial
   `time.schedule`) using durable behavior rather than one unbounded in-memory
   timer per reminder.
7. MPRIS media events with player identity, metadata stabilization, and
   deduplication.
8. Strict explicit event ingress suitable for user-owned Omarchy hook shims and
   future explicit screenshot producers.
9. Consolidated, explicitly scoped filesystem observation with precise create,
   modify, move, removal, degradation, and overflow semantics.
10. Trash and screenshot normalization where it fits coherently on the shared
    filesystem/ingress foundation.
11. Companion actions: `notification.show`, OSD, sound, literal `exec.argv`,
    listener state, and bounded event recording as supported by the selected
    architecture.
12. Machine-readable resource/privacy impact preflight and useful runtime
    diagnostics.
13. A functional minimal configuration/status surface or CLI. Prefer complete
    behavior and testability over visual polish.
14. Unit, fixture, schema, plugin, and source-level integration checks.

Resolve open implementation decisions pragmatically and record each decision
and rationale in the active Architect entry. Prefer the smallest architecture
that preserves the documented contracts. Do not add a resident helper merely
for convenience; if a helper is necessary, keep its ownership and lifecycle
explicit and measured.

## Hard boundaries

- Do not implement Provider mode or claim ownership of
  `org.freedesktop.Notifications`.
- Do not disable or replace `omarchy.notifications`.
- Do not modify `/usr/share/omarchy`.
- Do not install or enable the plugin in the user's live configuration.
- Do not install hooks, timers, services, packages, or dependencies on the
  host outside source-local/test-local behavior.
- Do not create a remote or commit unless the user separately requested it.
- Do not use unrestricted shell evaluation; keep command actions literal argv.
- Do not claim live or physical behavior that only fixtures established.
- Do not publish guessed memory numbers.

## Verification and handoff

- Run every safe source-level validation and test available.
- Use fixtures for platform events before live observation.
- Separate static, unit, fixture, source smoke, and live results.
- Inspect the final Git status and preserve unrelated changes.
- Update README, AGENTS, Architect assignment, handoff, active record, and todo
  to match the actual result.
- Record incomplete behavior honestly with exact next actions.
- Leave the repository in a coherent state even if a later adapter or UI polish
  must be deferred.
- Finish with a concise review summary containing implemented scope, tests,
  limitations, important files, and the next safest step.
