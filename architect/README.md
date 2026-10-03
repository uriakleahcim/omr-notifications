# Architect Directory

The `architect/` directory is a structured engineering-memory workspace for a software repository.

It stores planning records, investigations, design drafts, PRDs, implementation notes, inspection reports, blocked decisions, discontinued work, and resolved work records. It is broader than an `issues/` folder because not every entry is a bug. Some entries are feature plans, architecture changes, deferred ideas, refactors, research notes, audits, or future implementation packages.

The goal is to make project work resumable by a human or agent without needing the original chat history.

---

## Purpose

Use `architect/` to track:

- bugs
- PRDs
- feature plans
- refactor plans
- design decisions
- implementation drafts
- root-cause investigations
- inspection reports
- audits and scans
- deferred work
- blocked tasks
- discontinued work
- resolved engineering records
- future action-package ideas
- current assignment and handoff state

This directory should answer:

```txt
What was being worked on?
Why did it matter?
What context was known?
What decisions were made?
What changed?
How was it verified?
What remains unresolved?
What work was intentionally stopped?
```

---

## Importing the Architect Setup

When this README is maintained from a shared template repository, agents should prefer pulling the latest template instead of reconstructing the structure manually.

Recommended agent procedure:

1. Check whether the target repository already has an `architect/` directory.
2. If missing, install or copy the template from the shared architect-protocol repository.
3. Read `architect/README.md` before creating or updating architect entries.
4. Preserve any project-specific files already present under `architect/`.
5. Do not overwrite active handoff files unless the user explicitly requests a reset.

Recommended template source placeholders:

```txt
ARCHITECT_TEMPLATE_REPO=<owner>/<repo>
ARCHITECT_TEMPLATE_REF=main
ARCHITECT_TEMPLATE_PATH=templates/architect
```

Project-specific rules should live in a separate file such as:

```txt
architect/PROJECT.md
```

Do not put project-specific runtime details into this generic README unless the repository is not intended to be reusable.

---

## Naming Convention

Each architect entry folder should use:

```txt
YYYY-MM-DD-short-kebab-title
```

Examples:

```txt
2026-05-07-process-scan-log-storage-and-rotation
2026-05-04-json-window-title-escape-crash
2026-05-04-powershell-require-admin-hard-failure
```

Rules:

- Use the creation date.
- Keep the title short.
- Use lowercase kebab-case.
- Prefer specific names over generic names.
- Do not rename entries casually after creation unless the original title is misleading.
- Use `YYYY-MM-DD` date order. Do not use `YYYY-DD-MM`.

Report files use timestamped names:

```txt
architect/reports/<kind>-YYYY-MM-DD-HHmmss.md
```

Example:

```txt
architect/reports/redundant-code-inspection-2026-05-28-160820.md
```

---

## Directory Layout

```txt
architect/
├─ README.md
├─ PROJECT.md                         # optional project-specific rules
├─ ASSIGNMENT.md                      # current execution card
├─ HANDOFF.md                         # persistent assignment ledger
│
├─ reports/
│  ├─ SKILL.md                        # optional report/inspection skill
│  ├─ reports.registry.json
│  ├─ <kind>-YYYY-MM-DD-HHmmss.md
│  └─ .cache/
│     └─ <kind>-YYYY-MM-DD-HHmmss.md
│
├─ pending/
│  └─ YYYY-MM-DD-short-title/
│     ├─ meta.json
│     ├─ brief.md
│     ├─ prd.md                       # optional
│     ├─ plan.md                      # optional
│     ├─ todo.md
│     ├─ context.md
│     └─ blockers.md                  # optional
│
├─ active/
│  └─ YYYY-MM-DD-short-title/
│     ├─ meta.json
│     ├─ brief.md
│     ├─ plan.md
│     ├─ todo.md
│     ├─ context.md
│     ├─ notes.md
│     ├─ blockers.md                  # optional; used when status is blocked
│     └─ prd.md                       # optional
│
├─ resolved/
│  └─ YYYY-MM-DD-short-title/
│     ├─ meta.json
│     ├─ brief.md
│     ├─ assessment.md
│     ├─ fixes.md
│     ├─ verification.md
│     ├─ summary.md
│     └─ report-YYYY-MM-DD-HHmmss.md  # optional source-report copy
│
├─ discontinued/
│  └─ YYYY-MM-DD-short-title/
│     ├─ meta.json
│     ├─ brief.md
│     ├─ assessment.md                # optional
│     ├─ discontinued.md
│     ├─ summary.md
│     └─ report-YYYY-MM-DD-HHmmss.md  # optional source-report copy
│
└─ archived/
   └─ YYYY-MM-DD-short-title/
      ├─ meta.json
      ├─ brief.md
      └─ summary.md
```

---

# Root Handoff Files

Root handoff files preserve execution state across interrupted or multi-session work. They are not architect entries. They sit at the root of `architect/` because they describe the current assignment state, not one lifecycle folder.

Use these files when an agent or human needs to resume work without relying on chat history:

```txt
architect/ASSIGNMENT.md
architect/HANDOFF.md
```

Core split:

```txt
ASSIGNMENT.md = what to do next
HANDOFF.md    = why that is safe, what happened before, and what context must be preserved
```

The two files are paired, but they are not peers with the same purpose.

- `ASSIGNMENT.md` is the first-read execution card.
- `HANDOFF.md` is the second-read continuation ledger.

A future agent should be able to read `ASSIGNMENT.md` quickly, know the next safe action, then read `HANDOFF.md` only when they need the deeper context behind that action.

---

## `ASSIGNMENT.md`

`ASSIGNMENT.md` is the current execution card.

Read this file first when resuming work. It should be current, action-oriented, and compact enough to read before the first repository edit.

It answers:

```txt
What is active right now?
What exact step should happen next?
What files or areas are in scope?
What must not be touched?
What is the minimum verification baseline?
```

Use `ASSIGNMENT.md` for:

- current assignment status
- current branch and expected branch
- active objective ID and title
- primary architect entry path
- exact next action
- current slice and next slice
- current work scope
- active files likely to be edited or verified next
- immediate blockers
- immediate risks
- minimum verification baseline
- boundaries that must be respected before editing

Do not use `ASSIGNMENT.md` for:

- full historical ledger details
- long decision rationale
- full dirty worktree diagnostics
- complete test history
- complete file-change history
- complete terminal lifecycle records
- broad investigation notes
- full resumed-context commands

Those belong in `HANDOFF.md` or in the active, resolved, discontinued, or archived architect entry.

`ASSIGNMENT.md` may duplicate small operational facts from `HANDOFF.md`, but only when the next agent needs those facts before making the first edit.

### Recommended active structure

````md
# Architect Assignment

## Assignment Status
- assignmentStatus:
- lastUpdatedAt:
- updatedBy:
- currentBranch:
- expectedBranch:

## Current Objective
- objectiveId:
- objectiveTitle:
- objectiveStatus:
- primaryEntry:
- goal:
- completedSlice:
- currentSlice:
- nextSlice:
- completionCriteria:

## Current Architect Entries
- primary:
- active:
- pendingFollowUps:
- recentlyVerifiedResolved:
- related:

## Operational Boundaries
- shouldNotTouch:
- mustPreserve:
- blockedBy:
- immediateRisks:
- requiredBeforeEditing:

## Current Work Scope

| File / Area | State | Why It Matters For Next Action |
|---|---|---|

## Last Run Summary
- runEndedAt:
- outcome:
- workCompleted:
- workPartiallyCompleted:
- verificationSummary:
- commitCreated:

## Immediate Decisions
- Decision:
  - Effect On Next Action:

## Blockers
- none

## Immediate Risks
- none

## Next Action
Describe one exact next implementation, investigation, or verification step.

## Verification Baseline

```txt
# minimum commands needed to verify the next slice
```
````

### Idle or terminal structure

When there is no active objective, or the last objective is already `resolved`, `discontinued`, or `archived`, collapse `ASSIGNMENT.md` to a pointer-style card.

````md
# Architect Assignment

## Assignment Status
- assignmentStatus: idle
- lastUpdatedAt:
- updatedBy:
- currentBranch:
- expectedBranch:

## Last Terminal Objective
- objectiveId:
- objectiveTitle:
- objectiveStatus:
- terminalEntry:
- detailedHandoff: `architect/HANDOFF.md`

## Operational Boundaries
- shouldNotTouch:
- mustPreserve:
- immediateRisks:

## Current Work Scope

| File / Area | State | Why It Matters For Next Action |
|---|---|---|
| none | n/a | No active assignment. |

## Next Action
No active assignment. Create a new architect entry for any follow-up work before editing implementation files.

## Verification Baseline

```txt
# optional minimum repository health check, if known
```
````

Idle/terminal rules:

- Do not keep stale active files.
- Do not keep a full changed-files table.
- Do not keep full decisions, risks, or verification history.
- Keep only the terminal entry pointer, relevant boundaries, and next-action rule.
- Preserve `shouldNotTouch` only if it remains relevant to future work.

Update `ASSIGNMENT.md` at the end of every meaningful run, even when the run fails or only partially completes.

---

## `HANDOFF.md`

`HANDOFF.md` is the persistent assignment ledger.

Read this file after `ASSIGNMENT.md` when the next action depends on prior decisions, dirty worktree state, verification setup, blockers, risks, or partially completed implementation details.

It answers:

```txt
What happened before?
Why is the next action safe?
What changed?
What was intentionally preserved?
What decisions were made and why?
How was work verified?
What context must remain available?
```

Use `HANDOFF.md` for:

- detailed last run summary
- broader objective scope and non-goals
- related architect entries
- preserved dirty worktree areas
- full files-changed ledger from the last meaningful run
- unfinished files with safe next actions
- next files likely to touch
- decisions and rationale
- blockers and required resolution
- risks and mitigations
- local setup or verification prerequisites
- verification details and known gaps
- repository state notes
- resume commands
- commit status

`HANDOFF.md` may be longer than `ASSIGNMENT.md`, but it must still remain structured and scannable. Do not paste full architect entries into it. Link to the active, pending, resolved, discontinued, or archived entry paths instead.

### Recommended structure

````md
# Assignment Handoff

## Assignment Status
- assignmentStatus:
- lastUpdatedAt:
- updatedBy:
- currentBranch:
- expectedBranch:
- objectiveId:
- objectiveTitle:
- objectiveStatus:

## Current Architect Entries
- primary:
- active:
- pending:
- lastVerifiedCompleted:
- pendingFollowUps:
- related:
- blockedBy:
- shouldNotTouch:

## Objective Scope
- goal:
- scope:
- nonGoals:
- completionCriteria:
- currentLifecycleState:

## Last Run Summary
- runStartedAt:
- runEndedAt:
- outcome:
- workCompleted:
- workPartiallyCompleted:
- workNotStarted:
- testsRun:
- testResult:
- verificationSetup:
- commitCreated:
- commitHash:

## Files Changed By This Run

| File | State | Reason | Verification |
|---|---|---|---|

## Existing Dirty Work Preserved

| Area | State | Handling | Reason |
|---|---|---|---|

## Unfinished Files

| File | State | Remaining Work | Safe Next Action |
|---|---|---|---|

## Next Files To Touch

| File | Planned Change | Depends On | Boundary |
|---|---|---|---|

## Decisions Made
- Decision:
  - Rationale:
  - Alternatives Considered:
  - Consequence:
  - Recorded In:

## Blockers
- none

## Risks
- Risk:
  - Impact:
  - Mitigation:
  - Follow-Up:

## Verification Details

### Commands Run

```txt
# exact commands run during the last meaningful run
```

### Result

- status:
- summary:
- failures:
- skipped:
- environmentNotes:

### Manual Checks

- Check:

### Known Verification Gaps

- Gap:
  - Reason:
  - Safe Follow-Up:

## Repository State
- gitStatusSummary:
- branch:
- safeDirectoryRequired:
- untrackedFiles:
- modifiedFiles:
- stagedFiles:
- commitCreated:
- commitHash:

## Local Setup / Environment Notes
- os:
- shell:
- requiredServices:
- ports:
- environmentVariables:
- localPaths:
- setupCaveats:

## Next Action
Describe the next safest implementation, investigation, or verification step and the boundary it must stay within.

## Resume Commands

```txt
# commands needed to re-establish context or rerun verification
```

## Handoff Integrity Checklist
- [ ] `ASSIGNMENT.md` points to the current or terminal objective.
- [ ] `ASSIGNMENT.md` has exactly one clear next action or states idle.
- [ ] `HANDOFF.md` records detailed state needed to resume.
- [ ] Dirty worktree areas are recorded or explicitly marked not observed.
- [ ] Blockers are recorded or marked none.
- [ ] Risks have mitigations or follow-up paths.
- [ ] Verification commands and results are recorded.
- [ ] Commit state is recorded.
- [ ] No secrets or private tokens are included.
````

Update `HANDOFF.md` at the end of every meaningful run when any of the following changes:

- objective state
- implementation state
- dirty worktree handling
- active or related architect entries
- blocker state
- risk state
- verification setup
- repository state
- next safe action
- commit state

---

## Relationship Between `ASSIGNMENT.md` and `HANDOFF.md`

Do not use the two files as duplicate summaries.

Use this operational split:

```txt
ASSIGNMENT.md = what to do next
HANDOFF.md    = why that is safe, what happened before, and what context must be preserved
```

If the same information appears in both files, prefer this rule:

- Put the short operational version in `ASSIGNMENT.md`.
- Put the detailed historical, diagnostic, or safety-preservation version in `HANDOFF.md`.

Examples:

| Information | Goes In |
|---|---|
| Exact next action | Both, shorter in `ASSIGNMENT.md`; safer boundary in `HANDOFF.md` |
| Current objective ID/title/status | Both |
| Full dirty worktree notes | `HANDOFF.md` |
| Areas that must not be touched | Both, shorter in `ASSIGNMENT.md` |
| Full verification workaround | `HANDOFF.md` |
| Minimum test commands | `ASSIGNMENT.md` |
| Detailed test history | `HANDOFF.md` |
| File-by-file changed list | `HANDOFF.md`; only active next-scope files in `ASSIGNMENT.md` |
| Expected next files to edit | Both, shorter in `ASSIGNMENT.md` |
| Long rationale for decisions | `HANDOFF.md` |
| Immediate decision affecting next edit | `ASSIGNMENT.md`, with detail in `HANDOFF.md` |
| Resume commands | `HANDOFF.md` |
| Terminal objective closeout details | `HANDOFF.md` and terminal lifecycle entry |

### Terminal objective rule

When `objectiveStatus` is terminal and no next active slice exists, `ASSIGNMENT.md` must collapse to idle/terminal mode.

Do not keep full changed-file, decision, risk, or verification sections in `ASSIGNMENT.md` after an objective is closed. Keep those details in:

```txt
architect/HANDOFF.md
architect/resolved/<objective-id>/
architect/discontinued/<objective-id>/
architect/archived/<objective-id>/
```

### Drift rule

If `ASSIGNMENT.md` and `HANDOFF.md` disagree:

1. Trust lifecycle folders and `meta.json` first.
2. Trust `HANDOFF.md` for detailed prior-state context.
3. Trust `ASSIGNMENT.md` only for the intended next action after confirming it is not stale.
4. Update both root files before making implementation changes if the drift affects safety.

---

# Status Folders

## `reports/`

Use `reports/` for inspection outputs, audits, scans, and structured findings that have not necessarily become implementation work yet.

Reports are evidence records. Pending, active, resolved, discontinued, and archived architect entries are lifecycle records.

Good report candidates:

- redundant-code inspections
- security audits
- configuration drift reports
- dependency scans
- architecture consistency checks
- generated findings that may later become pending or active work

A report file should be timestamped so multiple reports can describe the same area at different times:

```txt
architect/reports/<kind>-YYYY-MM-DD-HHmmss.md
```

Example:

```txt
architect/reports/redundant-code-inspection-2026-05-28-160820.md
```

Reports should answer:

```txt
What was inspected?
When was it inspected?
What was found?
What evidence supports each finding?
What should become pending or active architect work?
What should not be changed without a design decision?
How should follow-up work be verified?
```

Reports should not directly replace `brief.md`, `assessment.md`, `plan.md`, or `fixes.md`. Instead, they feed those files when an architect entry is created or resolved.

Root report files are live evidence while any related architect entry is still `pending/`, `active/`, or `blocked`. After every related execution entry has reached a terminal lifecycle state such as `resolved/`, `discontinued/`, or `archived/`, preserve the report inside each terminal entry that needs the evidence and then move the root report file to the report cache:

```txt
architect/reports/.cache/<kind>-YYYY-MM-DD-HHmmss.md
```

The cache copy is an archival fallback only. Do not keep finalized root report files in `architect/reports/`, and do not keep finalized report nodes in `reports.registry.json`.

### `reports.registry.json`

The `reports/` directory should include a machine-readable registry:

```txt
architect/reports/reports.registry.json
```

The registry tracks:

- report IDs
- report paths
- report statuses
- summary counts
- related pending/active/resolved/discontinued/archived architect entries
- supersession relationships
- lifecycle events

Allowed report status values:

```txt
reported
triaged
promoted_pending
promoted_active
linked_existing
blocked
resolved
discontinued
archived
superseded
```

Recommended report event types:

```txt
REPORT_CREATED
REPORT_UPDATED
REPORT_TRIAGED
REPORT_SUPERSEDED
REPORT_ARCHIVED
REPORT_PROMOTED_TO_PENDING
REPORT_PROMOTED_TO_ACTIVE
REPORT_LINKED_TO_EXISTING_ARCHITECT
ARCHITECT_CREATED_PENDING
ARCHITECT_CREATED_ACTIVE
ARCHITECT_MOVED_TO_ACTIVE
ARCHITECT_BLOCKED
ARCHITECT_DISCONTINUED
ARCHITECT_RESOLVED
ARCHITECT_ARCHIVED
REPORT_COPIED_TO_RESOLUTION
REPORT_COPIED_TO_DISCONTINUATION
REPORT_COPIED_TO_ARCHIVE
REPORT_FINALIZED_TO_CACHE
REGISTRY_AUDITED
```

Starter registry:

```json
{
  "schemaVersion": 1,
  "updatedAt": null,
  "reports": []
}
```

Example `reports.registry.json`:

```json
{
  "schemaVersion": 1,
  "updatedAt": "2026-05-28T16:08:20-04:00",
  "reports": [
    {
      "id": "redundant-code-inspection-2026-05-28-160820",
      "kind": "redundant-code-inspection",
      "title": "Redundant / Unnecessary Code Inspection Report",
      "path": "architect/reports/redundant-code-inspection-2026-05-28-160820.md",
      "status": "reported",
      "createdAt": "2026-05-28T16:08:20-04:00",
      "updatedAt": "2026-05-28T16:08:20-04:00",
      "summary": {
        "totalFindings": 11,
        "safeRemovals": 0,
        "safeInlineCandidates": 0,
        "consolidationCandidates": 2,
        "lookupCacheCandidates": 3,
        "refactorCandidates": 3,
        "architectDecisionRequired": 0,
        "unknownUsageFindings": 6
      },
      "relatedArchitectEntries": [],
      "supersedes": [],
      "supersededBy": null,
      "events": [
        {
          "at": "2026-05-28T16:08:20-04:00",
          "type": "REPORT_CREATED",
          "note": "Initial redundant / unnecessary code inspection report created."
        }
      ]
    }
  ]
}
```

Keep the registry valid JSON. Do not add comments, Markdown, trailing commas, or full report bodies inside `reports.registry.json`.

The registry tracks live report workflow only. When a report is finalized into terminal architect entries and moved to `architect/reports/.cache/`, remove that report object from `reports.registry.json` and refresh `updatedAt`.

---

## `pending/`

Use `pending/` for work that is known but not currently being implemented.

Good candidates:

- future todos
- PRDs
- deferred ideas
- known design gaps
- unresolved bugs
- planned refactors
- user decisions needed later
- implementation ideas not yet started

A pending entry should usually include:

```txt
meta.json
brief.md
todo.md
context.md
```

Optional:

```txt
prd.md
plan.md
blockers.md
```

---

## `active/`

Use `active/` for work currently being investigated, designed, or implemented.

Good candidates:

- current debugging sessions
- active refactors
- open architecture changes
- partially implemented plans
- tasks with evolving notes
- entries requiring repeated agent/human updates

An active entry should usually include:

```txt
meta.json
brief.md
plan.md
todo.md
context.md
notes.md
```

Optional:

```txt
blockers.md
prd.md
```

Blocked work normally remains under `active/` with `status: "blocked"` in `meta.json` and a `blockers.md` file. Move it to `pending/` only when the work is no longer the active assignment.

---

## `resolved/`

Use `resolved/` for completed work.

A resolved entry should explain:

- what was reported or requested
- what caused it, if applicable
- what changed
- how it was verified
- what risks remain

A resolved entry should usually include:

```txt
meta.json
brief.md
assessment.md
fixes.md
verification.md
summary.md
```

If resolved work came from one or more reports, copy each source report into the resolved entry folder using:

```txt
report-YYYY-MM-DD-HHmmss.md
```

---

## `discontinued/`

Use `discontinued/` for work that was started, planned, or investigated but intentionally stopped before completion.

This is different from `archived/`:

- Use `discontinued/` when the work was valid enough to record, but the project decision is to stop pursuing it.
- Use `archived/` when the record itself is stale, obsolete, rejected, or preserved only for historical context.

Good candidates:

- work stopped because requirements changed
- work superseded by a different design
- implementation abandoned after investigation
- planned feature intentionally dropped
- report finding determined not worth implementing
- blocked work closed as no longer relevant

A discontinued entry should explain:

- what was being attempted
- why it was stopped
- what evidence or context led to the decision
- whether anything should be preserved
- whether there are future reopen conditions

A discontinued entry should usually include:

```txt
meta.json
brief.md
discontinued.md
summary.md
```

Optional:

```txt
assessment.md
verification.md
report-YYYY-MM-DD-HHmmss.md
```

Recommended `discontinued.md` structure:

```md
# Discontinued

## Decision
Describe the decision to stop the work.

## Reason
Explain why the work is no longer being pursued.

## Work Completed Before Stop
List any useful completed investigation, design, or implementation.

## Preserved Artifacts
List files, reports, branches, or notes that should remain available.

## Reopen Conditions
Describe conditions that would justify reopening this work, or write `none`.
```

---

## `archived/`

Use `archived/` for stale, rejected, obsolete, or intentionally abandoned records that should be preserved but should not be treated as current work.

Do not move completed work to `archived/` by default. Completed work belongs in `resolved/`.

Do not use `archived/` as a substitute for `discontinued/` when a planned or active work item is intentionally stopped and the stop decision itself matters.

A typical archived entry should include:

```txt
meta.json
brief.md
summary.md
```

---

# File Roles

## `PROJECT.md`

Optional project-specific rules.

Use this file for repository-specific implementation details that should not live in the generic architect protocol, such as:

- build commands
- test commands
- branch rules
- framework cautions
- module layout
- deployment constraints
- public API boundaries
- project-specific agent instructions

## `ASSIGNMENT.md`

Root-level current execution card.

Use this file to tell the next agent what is active, what exact action comes next, what files or areas are in scope, and what must not be touched.

`ASSIGNMENT.md` is the first-read file. It should contain the short operational answer to:

```txt
What should happen next?
```

It may duplicate a small amount of data from `HANDOFF.md`, but only when that data is needed before the next edit. It must not carry full ledger details after an objective becomes terminal.

## `HANDOFF.md`

Root-level persistent assignment ledger.

Use this file to preserve detailed continuation context across runs: dirty worktree handling, local verification requirements, risks, blockers, decisions, unfinished files, safe next actions, and resume commands.

`HANDOFF.md` is the second-read file. It should contain the detailed answer to:

```txt
Why is the next action safe, what happened before, and what context must be preserved?
```

`HANDOFF.md` should not replace the active architect entry. It should point to entries and summarize only the state needed to resume safely.

## `reports/*.md`

A report Markdown file is an evidence snapshot. It should capture findings, counts, affected files, risk, evidence strength, recommendations, and proposed architect entries.

Reports should not directly replace `brief.md`, `assessment.md`, `plan.md`, or `fixes.md`. They feed those files when an architect entry is created or resolved.

## `reports.registry.json`

Machine-readable report lifecycle registry.

Use this file for:

- report IDs and paths
- report status
- timestamps
- summary counters
- links from reports to architect entries
- report supersession
- report-to-architect promotion events
- terminal-copy events

Do not put full report bodies in `reports.registry.json`. Store live report bodies in `architect/reports/*.md`, finalized fallback copies in `architect/reports/.cache/*.md`, and terminal-entry report copies in the terminal entry folder.

## `meta.json`

Machine-readable lifecycle and indexing metadata.

Use this file for:

- status
- timestamps
- tags
- related entries
- source reports
- lifecycle events
- origin information
- grouping/search support

Do not put full investigation notes in `meta.json`.

Example:

```json
{
  "id": "2026-05-07-process-scan-log-storage-and-rotation",
  "title": "Process Scan Log Storage and Rotation",
  "status": "pending",
  "createdAt": "2026-05-07T02:10:00-04:00",
  "activatedAt": null,
  "resolvedAt": null,
  "discontinuedAt": null,
  "archivedAt": null,
  "updatedAt": "2026-05-07T02:10:00-04:00",
  "tags": [
    "logging",
    "audit",
    "jsonl",
    "storage"
  ],
  "related": [],
  "sourceReports": [],
  "origin": {
    "source": "chat",
    "summary": "Discussion about storing raw process evaluation logs over time for debugging and audit."
  },
  "events": [
    {
      "at": "2026-05-07T02:10:00-04:00",
      "type": "CREATED",
      "note": "Created from discussion about process scan log storage."
    }
  ]
}
```

Allowed `status` values:

```txt
pending
active
blocked
resolved
discontinued
archived
```

Recommended event types:

```txt
CREATED
MOVED_TO_PENDING
MOVED_TO_ACTIVE
UPDATED
BLOCKED
UNBLOCKED
RESOLVED
DISCONTINUED
REOPENED
ARCHIVED
RENAMED
LINKED
REPORT_LINKED
```

## `brief.md`

The core human-readable statement.

Use for:

- original request
- problem statement
- design goal
- expected behavior
- actual behavior
- affected files
- relevant logs
- reproduction steps
- scope boundaries

Keep `brief.md` mostly stable after creation. Put evolving thoughts in `notes.md`.

## `prd.md`

Product or implementation requirements.

Use for:

- goals
- problem statement
- requirements
- non-goals
- acceptance criteria
- future enhancements
- implementation constraints

Use `prd.md` when an entry describes future functionality, not just a bug fix.

## `todo.md`

Active checklist.

Use for:

- investigation tasks
- implementation tasks
- verification tasks
- user decisions still needed
- follow-up work

Example:

```md
# Todo

- [ ] Define scan log record shape.
- [ ] Add JSONL writer.
- [ ] Add size-based rotation.
- [ ] Add date-folder layout.
- [ ] Add gzip compression for rotated files.
- [ ] Add verification notes.
```

## `context.md`

Supporting background for humans and agents.

Use for:

- related files
- related entries
- architecture notes
- constraints
- assumptions
- previous decisions
- relevant command output
- chat-derived context
- known risks

This file should make future handoff easier.

## `plan.md`

Implementation or design plan.

Use when the entry needs staged execution.

Include:

- proposed approach
- affected modules
- data flow
- risks
- rejected alternatives
- migration notes
- ordering of work

## `notes.md`

Active investigation scratchpad.

Use for:

- temporary findings
- observations
- debugging notes
- partial theories
- open questions
- working thoughts

When resolving or discontinuing the entry, move important conclusions into terminal files such as:

```txt
assessment.md
fixes.md
verification.md
summary.md
discontinued.md
```

## `blockers.md`

Optional pause-state file.

Use only when progress is blocked by:

- missing information
- missing permissions
- unclear expected behavior
- unavailable reproduction data
- user decision required
- dependency not implemented yet

Example:

```md
# Blockers

## BLOCKED: User decision needed

The log writer cannot be finalized until a retention policy is chosen.

Options:

1. Keep logs for 7 days.
2. Keep logs for 30 days.
3. Keep logs until manually deleted.
```

## `assessment.md`

Root-cause, inspection, or system assessment.

Use after investigation.

Include:

- root cause, if applicable
- why it happened
- affected behavior
- affected files
- risk level
- alternatives considered
- final diagnosis

## `fixes.md`

Implementation record.

Use for:

- files changed
- functions/classes/modules changed
- behavior changes
- migration notes
- refactor notes
- compatibility notes

Example:

```md
# Fixes

## Files Changed

- `src/adapters/windows/WindowsProcessAdapter.ts`
- `src/types/policy.ts`

## Behavioral Changes

- The adapter no longer hard-fails when admin rights are unavailable.
- Missing privileged fields are treated as unavailable data instead of fatal errors.
```

## `verification.md`

Proof that the work was completed correctly.

Use for:

- tests run
- manual checks
- reproduction retry results
- edge cases checked
- remaining risks
- known limitations

Example:

```md
# Verification

## Manual Checks

- Re-ran observer CLI without admin rights.
- Confirmed process collection continues.
- Confirmed privileged fields degrade gracefully.

## Remaining Risks

- Some owner/user fields may remain unavailable without elevation.
```

## `discontinued.md`

Final stop-decision record.

Use when moving work to `discontinued/`.

Include:

- decision
- reason
- work completed before stopping
- preserved artifacts
- future reopen conditions

## `summary.md`

Final compact handoff.

Use for:

- one-paragraph problem summary
- cause or decision
- fix or stop reason
- result
- future follow-up

A future reader should be able to read only `summary.md` and understand the outcome.

---

# Lifecycle

Typical implementation flow:

```txt
pending -> active -> resolved
```

Blocked active work:

```txt
active -> blocked -> active -> resolved
```

Discontinued work:

```txt
pending -> discontinued
active -> discontinued
blocked -> discontinued
```

Archived work:

```txt
pending -> archived
active -> archived
resolved -> archived
discontinued -> archived
```

Reopened work:

```txt
resolved -> active
discontinued -> active
archived -> active
```

Report-backed flow:

```txt
reports/<report-id>.md
  -> reports.registry.json status: reported
  -> pending entry created, active entry created, or existing entry linked
  -> reports.registry.json status: promoted_pending, promoted_active, or linked_existing
  -> architect entry implemented, discontinued, or archived
  -> terminal entry exists under resolved/, discontinued/, or archived/
  -> source report copied into each terminal entry that needs the evidence
  -> when all related entries are terminal, move root report to reports/.cache/
  -> remove finalized report node from reports.registry.json
```

## Resuming Work From Handoff Files

When resuming an interrupted assignment:

1. Read `architect/ASSIGNMENT.md`.
2. Determine whether the assignment is active, blocked, terminal, or idle.
3. If active or blocked, read `architect/HANDOFF.md`.
4. Read the primary active architect entry referenced by those files.
5. Read `architect/PROJECT.md` if it exists.
6. Verify the branch and worktree state before editing.
7. Preserve any unrelated dirty worktree files.
8. Respect `shouldNotTouch` boundaries.
9. Start from the recorded `Next Action` unless the repository state proves it stale.
10. If `ASSIGNMENT.md` is idle or terminal, do not edit implementation files until a new architect entry is created or an existing entry is reopened.

Resumption rule:

```txt
ASSIGNMENT.md tells you what to do next.
HANDOFF.md tells you why that action is safe and what state must be preserved.
```

## Closing Out a Run

When stopping work, even temporarily:

1. Update the active architect entry with durable implementation notes.
2. Update `architect/HANDOFF.md` with detailed state, risks, dirty worktree handling, verification details, repository state, and resume commands.
3. Update `architect/ASSIGNMENT.md` with the compact execution card for the next run.
4. Record verification commands and results.
5. Record whether a commit was created.
6. If the objective is terminal and no next active slice exists, collapse `ASSIGNMENT.md` to idle/terminal mode.
7. Keep full terminal closeout details in `HANDOFF.md` and the terminal lifecycle entry, not in `ASSIGNMENT.md`.

Do not rely on chat history as the only handoff record.

## Creating a Report

When an inspection, audit, or scan produces findings:

1. Create a timestamped Markdown report under `architect/reports/`.
2. Create or update `architect/reports/reports.registry.json`.
3. Add a `REPORT_CREATED` or `REPORT_UPDATED` event.
4. Keep the report sanitized according to repository safety rules.
5. Do not create implementation changes from the report in the same pass unless explicitly requested.

## Promoting a Report to an Architect Entry

When a report finding becomes planned work:

1. Create the folder under `pending/` unless work begins immediately.
2. Create the folder under `active/` if implementation begins immediately.
3. Add normal architect files such as `meta.json`, `brief.md`, `todo.md`, and `context.md`.
4. Add `plan.md` when staged implementation is needed.
5. Add the report ID to the architect entry `meta.json` under `sourceReports`.
6. Add the architect entry ID to the report registry item under `relatedArchitectEntries`.
7. Append registry events such as `REPORT_PROMOTED_TO_PENDING`, `ARCHITECT_CREATED_PENDING`, `REPORT_PROMOTED_TO_ACTIVE`, or `ARCHITECT_CREATED_ACTIVE`.

Example architect `meta.json` report link:

```json
{
  "sourceReports": [
    "redundant-code-inspection-2026-05-28-160820"
  ]
}
```

## Resolving Report-Backed Work

When work from a report is resolved:

1. Move the architect entry to `resolved/`.
2. Finalize `assessment.md`, `fixes.md`, `verification.md`, and `summary.md`.
3. Copy each source report into the resolved folder.
4. Name each copied report using the report timestamp:

```txt
architect/resolved/YYYY-MM-DD-short-title/report-YYYY-MM-DD-HHmmss.md
```

5. Append `ARCHITECT_RESOLVED` and `REPORT_COPIED_TO_RESOLUTION` while the report remains live in `architect/reports/`.
6. If any related architect entry is still `pending/`, `active/`, or `blocked`, keep the root report file and registry node in place.
7. If every related architect entry is terminal, finalize the source report:
   - verify the report has been copied into each terminal entry that needs the evidence
   - move `architect/reports/<report-id>.md` to `architect/reports/.cache/<report-id>.md`
   - remove that report object from `architect/reports/reports.registry.json`
   - refresh the registry `updatedAt` timestamp and keep the JSON valid
8. Do not leave duplicate finalized report files in `architect/reports/`.

## Discontinuing Report-Backed Work

When work from a report is intentionally stopped:

1. Move the architect entry to `discontinued/`.
2. Finalize `discontinued.md` and `summary.md`.
3. Add `assessment.md` when the stop decision depends on investigation findings.
4. Copy each source report into the discontinued folder.
5. Name each copied report using the report timestamp:

```txt
architect/discontinued/YYYY-MM-DD-short-title/report-YYYY-MM-DD-HHmmss.md
```

6. Append `ARCHITECT_DISCONTINUED` and `REPORT_COPIED_TO_DISCONTINUATION` while the report remains live in `architect/reports/`.
7. If every related architect entry is terminal, move the root report to `architect/reports/.cache/` and remove the finalized report node from `reports.registry.json`.

## Archiving Report-Backed Work

When report-backed work is archived without resolution or discontinuation:

1. Move the architect entry to `archived/`.
2. Finalize `summary.md` with the archive reason.
3. Copy each source report into the archived folder if the evidence should remain with the terminal record.
4. Append `ARCHITECT_ARCHIVED` and `REPORT_COPIED_TO_ARCHIVE` when applicable.
5. If every related architect entry is terminal, move the root report to `architect/reports/.cache/` and remove the finalized report node from `reports.registry.json`.

## Creating an Entry

When creating a new entry:

1. Create the folder under `pending/` unless work begins immediately.
2. Add `meta.json`.
3. If created from a report, include `sourceReports` in `meta.json`.
4. Add `brief.md`.
5. Add `todo.md`.
6. Add `context.md` if there is meaningful background.
7. Add `prd.md` or `plan.md` when needed.

## Activating an Entry

When work begins:

1. Move the folder from `pending/` to `active/`.
2. Update `meta.json`:
   - `status: "active"`
   - `activatedAt`
   - `updatedAt`
   - append `MOVED_TO_ACTIVE` event
3. Add or update:
   - `plan.md`
   - `todo.md`
   - `notes.md`

## Blocking an Entry

When work cannot continue:

1. Keep the folder in `active/` unless it is deferred.
2. Add or update `blockers.md`.
3. Update `meta.json`:
   - `status: "blocked"`
   - `updatedAt`
   - append `BLOCKED` event

## Resolving an Entry

When work is complete:

1. Move the folder to `resolved/`.
2. If the entry came from one or more reports, copy each source report into the resolved folder as `report-YYYY-MM-DD-HHmmss.md`.
3. Update `meta.json`:
   - `status: "resolved"`
   - `resolvedAt`
   - `updatedAt`
   - append `RESOLVED` event
4. Add or finalize:
   - `assessment.md`
   - `fixes.md`
   - `verification.md`
   - `summary.md`

## Discontinuing an Entry

When work is intentionally stopped before completion:

1. Move the folder to `discontinued/`.
2. If the entry came from one or more reports, copy each source report into the discontinued folder as `report-YYYY-MM-DD-HHmmss.md`.
3. Update `meta.json`:
   - `status: "discontinued"`
   - `discontinuedAt`
   - `updatedAt`
   - append `DISCONTINUED` event
4. Add or finalize:
   - `discontinued.md`
   - `summary.md`
5. Preserve `assessment.md`, `plan.md`, `notes.md`, or `verification.md` if they are useful for the terminal record.

## Archiving an Entry

When an entry is stale, obsolete, rejected, or preserved only for history:

1. Move the folder to `archived/`.
2. Update `meta.json`:
   - `status: "archived"`
   - `archivedAt`
   - `updatedAt`
   - append `ARCHIVED` event
3. Add or finalize:
   - `summary.md`

## Reopening an Entry

When terminal work needs more changes:

1. Move the folder back to `active/`.
2. Update `meta.json`:
   - `status: "active"`
   - clear `resolvedAt`, `discontinuedAt`, or `archivedAt` only if the old terminal state is no longer valid
   - `updatedAt`
   - append `REOPENED` event
3. Add new notes to `notes.md`.
4. Preserve old terminal files unless they are misleading.

---

# Tagging Guidelines

Use tags to make future search, grouping, and agent reasoning easier.

Recommended tag groups:

## Area Tags

```txt
api
backend
build
cli
config
database
docs
frontend
infra
logging
security
tests
ui
worker
```

## Type Tags

```txt
bug
prd
refactor
design
investigation
audit
report
todo
decision
verification
performance
security
storage
```

## Status / Workflow Tags

```txt
blocked
needs-user-decision
future
mvp
post-mvp
manual-check-needed
discontinued
superseded
```

---

# Relationship Tracking

Use `meta.json.related` to connect entries.

Example:

```json
{
  "related": [
    "2026-05-07-policy-action-package-contract",
    "2026-05-07-process-scan-log-storage-and-rotation"
  ]
}
```

Use relationships for:

- parent/child work
- follow-up tasks
- similar bugs
- related architecture decisions
- PRDs that depend on another PRD
- fixes that came from the same root cause
- report findings that split into multiple entries
- discontinued work superseded by a replacement entry

Use `sourceReports` to connect architect entries back to report IDs.

---

# Entry Templates

## Root Handoff Template

```txt
architect/
├─ ASSIGNMENT.md
└─ HANDOFF.md
```

`ASSIGNMENT.md` is required for active/resumable work. `HANDOFF.md` is required when the work spans multiple runs, has dirty worktree constraints, has verification prerequisites, or includes partially completed implementation.

## Report Template

```txt
architect/reports/
├─ reports.registry.json
└─ <kind>-YYYY-MM-DD-HHmmss.md
```

A report may later be copied into one or more terminal entries:

```txt
architect/resolved/YYYY-MM-DD-short-title/
└─ report-YYYY-MM-DD-HHmmss.md
```

```txt
architect/discontinued/YYYY-MM-DD-short-title/
└─ report-YYYY-MM-DD-HHmmss.md
```

```txt
architect/archived/YYYY-MM-DD-short-title/
└─ report-YYYY-MM-DD-HHmmss.md
```

After all work sourced from the report reaches a terminal lifecycle state, move the root report file into the cache and remove its registry node:

```txt
architect/reports/.cache/
└─ <kind>-YYYY-MM-DD-HHmmss.md
```

## Pending PRD Template

```txt
architect/pending/YYYY-MM-DD-short-title/
├─ meta.json
├─ brief.md
├─ prd.md
├─ todo.md
└─ context.md
```

## Active Debugging Template

```txt
architect/active/YYYY-MM-DD-short-title/
├─ meta.json
├─ brief.md
├─ todo.md
├─ context.md
├─ notes.md
└─ blockers.md
```

## Active Refactor Template

```txt
architect/active/YYYY-MM-DD-short-title/
├─ meta.json
├─ brief.md
├─ plan.md
├─ todo.md
├─ context.md
└─ notes.md
```

## Resolved Bug Template

```txt
architect/resolved/YYYY-MM-DD-short-title/
├─ meta.json
├─ brief.md
├─ assessment.md
├─ fixes.md
├─ verification.md
├─ summary.md
└─ report-YYYY-MM-DD-HHmmss.md
```

## Discontinued Entry Template

```txt
architect/discontinued/YYYY-MM-DD-short-title/
├─ meta.json
├─ brief.md
├─ discontinued.md
├─ summary.md
└─ report-YYYY-MM-DD-HHmmss.md
```

## Archived Entry Template

```txt
architect/archived/YYYY-MM-DD-short-title/
├─ meta.json
├─ brief.md
└─ summary.md
```

---

# Rules

## Keep the Protocol Project-Agnostic

This README should describe reusable architect workflow rules.

Put repository-specific behavior in `architect/PROJECT.md` or in a dedicated project skill file.

Avoid hardcoding:

- project names
- framework names
- language-specific commands
- private repository paths
- hostnames
- deployment details
- vendor-specific runtime assumptions

## Keep Root Handoff Files Distinct

`ASSIGNMENT.md` and `HANDOFF.md` must not become two copies of the same summary.

Use this split:

```txt
ASSIGNMENT.md = what to do next
HANDOFF.md    = why that is safe, what happened before, and what context must be preserved
```

When updating both files:

- write the exact next action in both;
- keep the shortest operational form in `ASSIGNMENT.md`;
- keep detailed reasoning, dirty worktree notes, verification setup, repository state, and resume commands in `HANDOFF.md`;
- move terminal objective details out of `ASSIGNMENT.md` after closeout;
- collapse `ASSIGNMENT.md` to idle/terminal mode when no active slice remains.

If the two files drift, reconcile them before editing implementation files.

## Keep Reports Separate From Execution Entries

Reports are evidence snapshots. Pending and active architect entries are execution plans. Resolved, discontinued, and archived entries are terminal lifecycle records.

Do not treat a report as implementation approval by itself. Promote the relevant finding into `pending/` or `active/`, link it in `reports.registry.json`, and keep the report available for audit.

## Keep the Report Registry Auditable

Whenever a report is created, triaged, promoted, linked, superseded, archived, copied to a terminal entry, or finalized to cache, append an event to `architect/reports/reports.registry.json`.

When a report's related execution entries are all terminal, finish the registry audit before deletion:

1. Confirm the terminal-entry report copies exist where needed.
2. Move the root report to `architect/reports/.cache/`.
3. Remove the report node from `reports.registry.json`.
4. Refresh `updatedAt`.
5. Keep the JSON valid.

Do not keep a finalized report node solely to preserve event history. The terminal entry copy is the primary historical record. The `.cache/` file is only a fallback for the original root report after the live workflow is complete.

## Keep Entries Focused

Prefer one focused entry per concern.

Good:

```txt
2026-05-07-process-scan-log-storage-and-rotation
2026-05-07-policy-action-package-contract
```

Avoid:

```txt
2026-05-07-fix-logging-and-actions-and-ledger-and-cli
```

## Keep `brief.md` Stable

`brief.md` should preserve the original problem or goal.

Do not rewrite it every time the plan changes.

## Put Evolving Work in the Right File

Use:

```txt
notes.md         -> temporary thoughts
blockers.md      -> pause-state or blocking details
todo.md          -> checklist
plan.md          -> structured implementation path
assessment.md    -> final diagnosis or system assessment
fixes.md         -> final implementation record
verification.md  -> proof and checks
summary.md       -> final handoff
discontinued.md  -> stop decision and rationale
```

## Do Not Hide Decisions in Chat

If a decision affects future implementation, write it into one of:

```txt
context.md
plan.md
assessment.md
summary.md
discontinued.md
```

## Keep `meta.json` Parseable

`meta.json` must remain valid JSON.

Do not add comments, trailing commas, Markdown, or large notes.

## Prefer Markdown for Human Context

Use Markdown files for explanations, plans, reports, and summaries.

Use JSON only for metadata that future tooling should parse.

---

# Future Tooling Ideas

The `architect/` structure is designed to support later automation.

Possible future commands:

```txt
architect list --status pending
architect list --status active
architect list --status discontinued
architect list --tag logging
architect open 2026-05-07-process-scan-log-storage-and-rotation
architect related 2026-05-07-policy-action-package-contract
architect move --to active 2026-05-07-process-scan-log-storage-and-rotation
architect move --to discontinued 2026-05-07-abandoned-design-path
architect summarize --status resolved
architect summarize --status discontinued
architect handoff show
architect handoff update
architect assignment show
architect assignment update
architect reports list
architect reports audit-registry
architect reports promote redundant-code-inspection-2026-05-28-160820 --to pending
architect reports copy-to-resolution redundant-code-inspection-2026-05-28-160820 2026-05-28-transport-parsing-consolidation
architect reports copy-to-discontinued redundant-code-inspection-2026-05-28-160820 2026-05-28-abandoned-cleanup-path
architect reports finalize redundant-code-inspection-2026-05-28-160820
```

Potential future uses:

- track report-to-architect promotion
- audit unresolved reports
- preserve source reports inside terminal entries
- move finalized source reports into `reports/.cache/`
- generate changelogs
- find related bugs
- group similar failures
- track unresolved design decisions
- track discontinued decisions
- produce agent handoff summaries
- validate `ASSIGNMENT.md` and `HANDOFF.md` freshness
- detect drift between root handoff files and active entries
- build a local project knowledge graph
- calculate time from creation to resolution
- identify recurring subsystem problems

---

# Recommended Minimum Entry

For resumable active work, maintain:

```txt
architect/ASSIGNMENT.md
architect/HANDOFF.md
```

For most new reports, start with:

```txt
architect/reports/reports.registry.json
architect/reports/<kind>-YYYY-MM-DD-HHmmss.md
```

For most new entries, start with:

```txt
meta.json
brief.md
todo.md
context.md
```

Add other files only when needed.

For very small tasks, this is enough:

```txt
meta.json
brief.md
todo.md
```

For resolved records, aim to end with:

```txt
meta.json
brief.md
assessment.md
fixes.md
verification.md
summary.md
```

For discontinued records, aim to end with:

```txt
meta.json
brief.md
discontinued.md
summary.md
```
