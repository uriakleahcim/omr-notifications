# Architect Assignment

## Assignment Status

- assignmentStatus: active
- lastUpdatedAt: 2026-10-03T14:59:00-04:00
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
- completedSlice: Source-complete v0.2 runtime with rich notification actions,
  a privacy-minimized Codex completion bridge, icon asset, tests, and docs.
- currentSlice: The v0.2 snapshot and Codex notifier are installed and live in
  Omarchy Shell with one Companion owner and a verified end-to-end popup.
- nextSlice: Observe a real completion from a newly started Codex CLI process;
  consider richer UI authoring separately.
- completionCriteria: Source and authorized live behavior are both verified;
  future integrations retain separate approval and verification boundaries.

## Current Architect Entries

- primary:
  `architect/active/2026-10-02-omr-notifications-event-policy-engine`
- active: `2026-10-02-omr-notifications-event-policy-engine`
- pendingFollowUps: Provider mode; richer configuration UI; native MPRIS and
  inotify backends; controlled resource measurements
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

- runEndedAt: 2026-10-03T14:59:00-04:00
- outcome: rich notifications and Codex completion notifications live-verified
- workCompleted: Added Keymap-level notification options, strict validation,
  confined image handling, Codex ingress mapping/configuration, and live setup.
- workPartiallyCompleted: Native MPRIS/inotify, cron expressions, graphical
  policy editing, and resource measurement remain follow-ups.
- verificationSummary: 40 unit/fixture tests pass; Python compiles; all JSON
  parses; example and live preflight are ready; one live Codex event completed
  with zero failed actions and one Companion owner.
- commitCreated: v0.2 implementation commit (see Git history)

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

Start a new Codex CLI process and observe its first natural response-complete
callback. The supported user-level `notify` hook is already configured; the
current Codex process may retain its startup configuration until restarted.

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
