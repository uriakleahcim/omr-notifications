# Skill: Redundant / Unnecessary Code Inspection

## Purpose

Use this skill to inspect a repository for code, configuration, abstractions, or project files that appear redundant, duplicated, obsolete, over-complicated, or poorly consolidated.

This is an **inspection and reporting skill**, not an implementation skill.

Do not delete, rewrite, or refactor code during the first pass unless the user explicitly asks for implementation. The expected output is a structured Markdown report plus a registry update under `architect/reports/`.

---

## Goal

Identify project areas that can potentially be:

- removed
- simplified
- consolidated
- cached
- moved into clearer abstractions
- converted into focused follow-up architect entries

The inspection must preserve runtime behavior. Treat indirect usage paths conservatively.

---

## Required Inputs

Before starting, inspect the repository enough to determine:

- the primary language or languages
- build/test tools
- framework registration patterns
- public API boundaries
- plugin or extension mechanisms
- generated-code locations
- test and fixture structure
- existing `architect/` conventions, if present

If `architect/README.md` exists, follow its report lifecycle rules.

---

## Core Safety Rule

Do **not** mark code as removable only because a simple text search or static reference search shows no direct references.

Many projects use indirect runtime paths, including:

- dependency injection
- framework auto-discovery
- annotations, decorators, or attributes
- plugin manifests
- route registration
- generated code
- reflection
- service loaders
- package exports
- dynamic imports
- command registries
- build hooks
- test fixtures
- migration files
- public API contracts

When in doubt, classify as `UNKNOWN_USAGE`, `KEEP_PUBLIC_API`, `KEEP_REFLECTION_USED`, or `NEEDS_ARCHITECT_DECISION`.

---

## Inspection Scope

Inspect for the following categories.

### 1. Duplicate Logic

Look for repeated or near-repeated behavior, including:

- builders
- mappers
- validators
- serializers
- schema generators
- registry lookups
- dispatch or routing paths
- configuration parsing
- error construction
- response envelopes
- authorization or policy checks
- file/path handling
- test setup utilities

Group duplicate findings by behavior, not just by syntax.

### 2. Redundant Lookups

Identify repeated lookups or scans that may be safely cached, memoized, moved to startup, or consolidated.

Examples:

- repeated registry scans
- repeated metadata introspection
- repeated route or command resolution
- repeated schema generation
- repeated configuration reads
- repeated environment-variable resolution
- repeated file-system scans
- repeated package/module discovery
- repeated object serialization/deserialization
- repeated authorization or policy evaluation

For each lookup, determine:

- where it runs
- how often it runs
- whether it is startup-only, per-request, per-command, per-file, or per-test
- whether inputs are stable
- whether caching would require invalidation
- what could break if cached incorrectly

### 3. Dead or Obsolete Code

Look for code that appears no longer active, including:

- classes, functions, methods, fields, constants, scripts, or config keys
- old experimental paths replaced by newer architecture
- TODOs tied to abandoned designs
- compatibility shims that no longer have callers
- duplicated command wrappers
- obsolete tests or fixtures
- unused generated files
- unused documentation fragments

Do not recommend removal until indirect usage has been checked.

### 4. Overlapping Abstractions

Look for abstractions that perform the same conceptual role, including:

- multiple registries for the same objects
- multiple descriptor models for the same API
- duplicate DTOs or records
- multiple result wrappers or error envelopes
- parallel config models
- overlapping service classes
- interfaces with one implementation and no clear extension point
- helper utilities that obscure simple behavior

### 5. Unnecessary Complexity

Identify complexity that does not appear to provide equivalent value, including:

- deep call chains with no meaningful behavior
- premature extension points
- overly generic APIs
- reflection where direct metadata is already available
- manual JSON or object construction duplicating existing helpers
- excessive adapters around stable internal models
- configuration indirection without runtime benefit
- defensive layers that duplicate validation already performed elsewhere

### 6. Configuration Drift

Inspect project configuration for drift, including:

- declared settings that are not consumed
- consumed settings that are not documented
- defaults split across code, docs, config files, and scripts
- environment variables with inconsistent names
- feature flags that no longer guard behavior
- security, audit, or policy settings that are declared but unenforced
- build settings that no longer affect output
- stale sample config values

### 7. Metadata / Schema / Contract Drift

Inspect declared metadata and runtime behavior for mismatch.

Depending on the project, this may include:

- annotations
- decorators
- attributes
- manifests
- package exports
- route schemas
- command schemas
- OpenAPI specs
- GraphQL schemas
- protocol descriptors
- generated types
- validation schemas
- public documentation

Look for fields that are declared but unused, used but undocumented, or duplicated across multiple metadata systems.

---

## Language and Framework Adaptation

Adapt the inspection to the repository’s actual technology stack.

| Stack | Usage paths to check |
|---|---|
| Java / Kotlin | annotations, reflection, service loaders, dependency injection, Maven/Gradle config, generated sources |
| Spring / Micronaut / Quarkus | bean registration, auto-configuration, conditional beans, configuration properties |
| Node / TypeScript | package exports, route registration, decorators, build scripts, tsconfig paths, dynamic imports |
| Python | decorators, entry points, dynamic imports, pyproject metadata, framework registration |
| .NET | dependency injection, attributes, reflection, source generators, project files |
| Go | public packages, build tags, generated files, interface implementations |
| Rust | feature flags, public modules, macros, generated code, crate exports |
| Frontend apps | routes, components, hooks, stores, generated clients, CSS/theme tokens, build-time imports |
| CLI tools | command registries, shell scripts, config files, environment variables, install scripts |

These examples are not exhaustive. Use the repository’s actual conventions.

---

## Inspection Procedure

### Phase 1 — Build the Execution Map

Identify the main runtime or build-time paths.

```txt
startup / bootstrap
  -> configuration loading
  -> module discovery
  -> registry construction
  -> descriptor/schema generation
  -> public listing or routing
  -> command/request invocation
  -> validation / authorization / policy checks
  -> execution
  -> result serialization
```

Record the files, classes, functions, modules, scripts, or config files involved in each stage.

### Phase 2 — Build the Lookup Map

Find lookup, scan, introspection, or resolution points.

```txt
Module discovery
Registry lookup
Route lookup
Command lookup
Schema lookup
Config lookup
Environment lookup
Secret lookup
Metadata introspection
File-system scan
Generated descriptor lookup
Permission/policy lookup
Serialization conversion
```

For each lookup, answer:

```txt
Where is it called?
How often can it run?
Is it repeated for the same input?
Is it startup-only, per-request, per-command, per-file, or per-test?
Can it be cached or moved safely?
Does it need invalidation?
What could break if it is cached incorrectly?
```

### Phase 3 — Detect Duplication

Search for repeated patterns in:

```txt
metadata parsing
schema generation
validation
routing
dispatch
registry access
configuration resolution
result construction
error construction
authorization checks
policy/scope checks
logging/audit logic
test setup
manual serialization
```

Group findings by behavior.

### Phase 4 — Validate True Usage

Before recommending removal, check:

1. Direct code references.
2. Framework registration.
3. Dependency injection registration.
4. Plugin manifests.
5. Route or command registration.
6. Package/module exports.
7. Generated-code references.
8. Reflection or dynamic import usage.
9. Build scripts.
10. Tests and fixtures.
11. Documentation examples.
12. Public API compatibility.
13. Runtime-loaded or extension modules, if applicable.

### Phase 5 — Classify Findings

Classify each finding using one of these values:

```txt
SAFE_REMOVE
SAFE_INLINE
SAFE_CONSOLIDATE
LOOKUP_CACHE_CANDIDATE
NEEDS_REFACTOR
NEEDS_ARCHITECT_DECISION
KEEP_PUBLIC_API
KEEP_FRAMEWORK_REGISTERED
KEEP_REFLECTION_USED
KEEP_GENERATED_CODE
KEEP_TEST_SUPPORT
UNKNOWN_USAGE
```

Use conservative classification when runtime behavior is uncertain.

---

## Report Requirements

Write a Markdown report to a timestamped file under:

```txt
architect/reports/<kind>-YYYY-MM-DD-HHmmss.md
```

For this skill, use this report kind unless the user specifies another:

```txt
redundant-code-inspection
```

Example:

```txt
architect/reports/redundant-code-inspection-2026-05-28-160820.md
```

The report must include the full inspection result. Do not only print the report in chat or terminal output.

---

## Registry Requirements

Create or update:

```txt
architect/reports/reports.registry.json
```

If the registry does not exist, create it using:

```json
{
  "schemaVersion": 1,
  "updatedAt": null,
  "reports": []
}
```

Add or update a report item with this shape:

```json
{
  "id": "redundant-code-inspection-YYYY-MM-DD-HHmmss",
  "kind": "redundant-code-inspection",
  "title": "Redundant / Unnecessary Code Inspection Report",
  "path": "architect/reports/redundant-code-inspection-YYYY-MM-DD-HHmmss.md",
  "status": "reported",
  "createdAt": "YYYY-MM-DDTHH:mm:ssZ",
  "updatedAt": "YYYY-MM-DDTHH:mm:ssZ",
  "summary": {
    "totalFindings": 0,
    "safeRemovals": 0,
    "safeInlineCandidates": 0,
    "consolidationCandidates": 0,
    "lookupCacheCandidates": 0,
    "refactorCandidates": 0,
    "architectDecisionRequired": 0,
    "unknownUsageFindings": 0
  },
  "relatedArchitectEntries": [],
  "supersedes": [],
  "supersededBy": null,
  "events": [
    {
      "at": "YYYY-MM-DDTHH:mm:ssZ",
      "type": "REPORT_CREATED",
      "note": "Initial redundant / unnecessary code inspection report created."
    }
  ]
}
```

Keep `reports.registry.json` valid JSON.

Do not add comments, Markdown, trailing commas, or full report bodies to the registry.

---

## Report Format

Write the report using this structure:

```md
# Redundant / Unnecessary Code Inspection Report

## Summary

- Report ID:
- Created at:
- Repository:
- Branch:
- Commit:
- Inspection scope:
- Total findings:
- Safe removals:
- Safe inline candidates:
- Consolidation candidates:
- Lookup/cache candidates:
- Refactor candidates:
- Architect decision required:
- Unknown-usage findings:

## Inspection Method

Describe what was inspected and how usage was validated.

## Execution Map

| Phase | Files / Symbols | Notes |
|---|---|---|

## Lookup Hotspots

| ID | Lookup | Location | Frequency | Risk | Recommendation |
|---|---|---|---:|---|---|

## Duplicate Logic Findings

| ID | Area | Files / Symbols | Problem | Recommendation | Classification | Risk |
|---|---|---|---|---|---|---|

## Dead / Obsolete Code Candidates

| ID | Symbol | File | Evidence | Classification | Recommended Action | Risk |
|---|---|---|---|---|---|---|

## Overlapping Abstractions

| ID | Abstractions | Files | Overlap | Recommendation | Classification |
|---|---|---|---|---|---|

## Unnecessary Complexity

| ID | Area | Files / Symbols | Complexity | Simpler Direction | Classification |
|---|---|---|---|---|---|

## Configuration Drift

| ID | Property / Config | Declared In | Consumed By | Gap | Recommendation |
|---|---|---|---|---|---|

## Metadata / Schema / Contract Drift

| ID | Metadata / Contract | Expected Use | Actual Use | Gap | Recommendation |
|---|---|---|---|---|---|

## Recommended Refactor Packages

### Package 1 — Short Name

**Goal:**

**Files affected:**

**Why:**

**Risk:**

**Verification:**

## Proposed Architect Entries

List follow-up entries that should be created if the findings become planned work.

Use paths like:

```txt
architect/pending/YYYY-MM-DD-short-title/
```

For each proposed entry, include:

- title
- reason
- source finding IDs
- suggested files:
  - `meta.json`
  - `brief.md`
  - `todo.md`
  - `context.md`
  - `plan.md` when staged implementation is needed

## Verification Plan

- [ ] Run the repository’s standard build command.
- [ ] Run the repository’s standard test command.
- [ ] Run lint/static analysis, if configured.
- [ ] Run smoke checks for public entry points.
- [ ] Verify core invocation or runtime paths still work.
- [ ] Verify plugin/extension registration, if the project supports it.
- [ ] Verify public API compatibility where applicable.
- [ ] Verify generated metadata or schemas still match runtime behavior.

## Findings Requiring Human Decision

List any finding that should not be changed without project-owner approval.

## Non-Findings / Things Intentionally Kept

List inspected areas that looked suspicious but should be kept because they are public API, framework-registered, reflection-used, generated, test support, compatibility support, or otherwise intentional.

## Final Notes

Summarize the safest next step.
```

---

## Finding Detail Requirements

For every non-trivial finding, include enough evidence to make it actionable.

Each finding should answer:

```txt
What is the file path?
What is the class/function/symbol/config key?
What evidence supports the finding?
Why is it redundant, duplicated, obsolete, or over-complicated?
Is it safe to remove or change now?
What could break?
How should it be verified?
Does it require a follow-up architect entry?
```

Do not use vague phrases like:

```txt
probably unused
seems unnecessary
maybe redundant
```

unless the finding is explicitly classified as `UNKNOWN_USAGE` and the uncertainty is explained.

---

## Hard Rules

- Do not delete code during the first inspection pass.
- Do not rewrite large areas during the first inspection pass.
- Do not remove public API without explicit approval.
- Do not remove framework-registered code without checking registration paths.
- Do not remove reflection-used or dynamically loaded code without proof.
- Do not remove generated code unless the generator and consumers are understood.
- Do not remove tests or fixtures unless their purpose is confirmed obsolete.
- Prefer small refactor packages over one large cleanup.
- Any non-trivial cleanup should become an `architect/` entry before implementation.
- Keep report evidence specific and file-based.
- Keep the registry valid JSON.

---

## Final Output Requirement

After writing the report file and updating the registry, print only:

```txt
Inspection report written to architect/reports/<report-id>.md
```
