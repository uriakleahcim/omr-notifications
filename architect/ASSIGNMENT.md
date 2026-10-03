# Architect Assignment

## Assignment Status

- assignmentStatus: active
- lastUpdatedAt: 2026-10-03T14:26:00-04:00
- updatedBy: Codex
- currentBranch: main
- expectedBranch: main

## Current Objective

- objectiveId: `2026-10-02-omr-notifications-event-policy-engine`
- objectiveTitle: OmR Notifications Event-Policy Engine
- objectiveStatus: active
- primaryEntry:
  `architect/active/2026-10-02-omr-notifications-event-policy-engine`
- goal: Deliver a bounded, deterministic Companion-mode event-policy runtime
  for Omarchy without taking over the desktop notification provider.
- completedSlice: Source-complete v0.1 runtime, CLI, plugin host, schemas,
  examples, documentation, unit/fixture tests, and isolated dry-run smoke test.
- currentSlice: The reviewed source snapshot is installed, enabled, and live in
  Omarchy Shell with one Companion owner and a responding status panel.
- nextSlice: Review a narrowly scoped Codex CLI response-complete event source
  with the user before choosing an ingress or hook integration.
- completionCriteria: Source and authorized live behavior are both verified;
  future integrations retain separate approval and verification boundaries.

## Current Architect Entries

- primary:
  `architect/active/2026-10-02-omr-notifications-event-policy-engine`
- active: `2026-10-02-omr-notifications-event-policy-engine`
- pendingFollowUps: Codex CLI response-complete integration; Provider mode;
  richer configuration UI; native MPRIS and inotify backends; controlled
  resource measurements
- recentlyVerifiedResolved: none
- related: none

## Operational Boundaries

- shouldNotTouch: `/usr/share/omarchy`, user hooks, user systemd units, package
  state, or notification ownership; preserve the reviewed installed snapshot
- mustPreserve: Companion-only provider boundary; literal argv; XDG mutable
  data; transactional configuration; deterministic policy semantics
- blockedBy: none for the current Companion-mode slice
- immediateRisks: presenting polling/fixture results as native/live behavior or
  enabling sensitive listeners without an impact fingerprint
- requiredBeforeEditing: inspect Git status and the active entry; preserve the
  user's uncommitted scaffold and implementation

## Current Work Scope

| File / Area | State | Why It Matters |
| --- | --- | --- |
| `src/omr_notifications/` | implemented | Contracts, adapters, policies, actions, persistence, IPC |
| `manifest.json`, `Service.qml`, `Panel.qml` | implemented, installed, live | Omarchy host and minimal status surface |
| `schemas/` | implemented | Versioned public contracts |
| `examples/` | implemented | Safe source configuration and fixture |
| `tests/` | passing | Deterministic source/fixture verification |

## Last Run Summary

- runEndedAt: 2026-10-03T14:26:00-04:00
- outcome: source implementation live-verified and prepared for initial publish
- workCompleted: Implemented Companion v0.1, activated the Architect record,
  documented decisions, and ran source plus isolated socket/control smoke tests.
- workPartiallyCompleted: Native MPRIS/inotify, cron expressions, graphical
  policy editing, and resource measurement remain follow-ups.
- verificationSummary: 30 unit/fixture tests pass; Python compiles; all JSON
  parses; config/preflight/CLI, dry-run ingress/control, live QML IPC,
  single-instance ownership, and Omacale toast fallback were exercised.
- commitCreated: initial repository snapshot (this commit)

## Immediate Decisions

- Decision: Keep the hybrid Python/QML deployment.
  - Effect On Next Action: Install the whole repository as one plugin checkout;
    do not extract the QML or runtime into separate mutable locations.
- Decision: Resource-sensitive listeners and command policies fail closed.
  - Effect On Next Action: Review preflight fingerprints before adding them to
    `impactAcknowledgements`.

## Blockers

- No blocker for the current Companion-mode slice.

## Next Action

Discuss the Codex CLI completion source and payload boundary with the user.
Prefer an explicit local ingress event over process scraping if Codex exposes a
supported completion hook; then add the smallest matching listener and policy.

## Verification Baseline

```bash
PYTHONPATH=src python3 -m unittest discover -v
python3 -m compileall -q src tests
python3 bin/omr-notifications config validate examples/config.example.json
python3 bin/omr-notifications preflight examples/config.example.json
find . -name '*.json' -not -path './.git/*' -print0 | xargs -0 -n1 python3 -m json.tool >/dev/null
git diff --check
git status --short --branch
```
