# Architecture

## 1. Architectural Intent

OmR Notifications is a local event-policy runtime for Omarchy. It should make
desktop automation explainable and bounded:

```text
observe a configured source
  -> normalize one immutable event
  -> evaluate deterministic policies
  -> dispatch bounded actions
  -> expose health, suppression, and results
```

The core architecture must not depend on one choice of persistence backend or
whether every component ultimately runs inside `omarchy-shell`. Those are
deployment decisions around stable domain contracts.

## 2. System Context

```text
                         user-owned configuration
                                  |
                                  v
                         Configuration Manager
                                  |
                                  v
Omarchy hooks ---> Ingress ----> Runtime Coordinator <---- Status / Setup UI
systemd timers ---> Adapter ---> Event Queue
MPRIS -----------> Adapter          |
inotify ---------> Adapter          v
Trash metadata --> Adapter      Policy Engine
screenshot ------> Adapter          |
                                     v
                              Action Dispatcher
                         /       |       |       \
                notification   OSD    sound   literal argv
                         \       |       |       /
                                  v
                           Results / Journal
```

In Companion mode, `notification.show` delegates to the active Omarchy
notification service. OmR does not own `org.freedesktop.Notifications`.

## 3. Deployment Boundary

### Required shell-facing component

A third-party Omarchy service plugin is expected to provide:

- lifecycle within `omarchy-shell`;
- setup/status UI integration where appropriate;
- MPRIS integration or a bridge to it;
- Companion-mode notification/OSD dispatch;
- local IPC/control endpoints permitted by the plugin contract;
- health and diagnostics surfaced to the user.

### Optional companion component

A companion CLI or process may be justified for:

- strict schema validation outside QML;
- durable systemd timer reconciliation;
- consolidated filesystem watching;
- persistence with atomic append/query behavior;
- controlled resource measurement;
- activation flows that must occur before plugin code is loaded.

The presence, language, and lifetime of such a component are unresolved. Code
must keep the domain contracts independent from that choice. A helper cannot be
silently installed or enabled merely because the architecture permits one.

### Why not decide placement prematurely

An all-QML runtime reduces packaging but shares memory attribution with the
shell and may rely on subprocesses for filesystem/systemd work. A companion
runtime improves isolation and persistence options but adds a resident process,
IPC, packaging, and lifecycle complexity. Activation should decide using a
prototype and measured evidence.

## 4. Logical Components

### Runtime Coordinator

Owns the active configuration revision and orchestrates adapters, the queue,
policy engine, actions, persistence, health, pause state, and shutdown. It does
not contain adapter-specific parsing or action-specific execution.

Responsibilities:

- accept a validated configuration snapshot;
- compute the listener/adaptor reconciliation plan;
- start new adapters before retiring no-longer-needed adapters when safe;
- expose current revision and last known-good revision;
- route accepted events to the queue;
- pause side effects without deleting configuration;
- coordinate bounded shutdown and startup reconciliation.

### Configuration Manager

Loads, validates, migrates, and atomically publishes configuration snapshots.

Pipeline:

```text
read candidate
  -> parse
  -> migrate in memory
  -> structural validation
  -> semantic/cross-reference validation
  -> impact calculation
  -> optional user acknowledgement
  -> atomic publish
  -> persist last known-good revision
```

Failures never partially update the live runtime.

### Adapter Registry

Maps stable adapter type IDs to factories and schemas. Adapter types are
registered explicitly; dynamic arbitrary imports are not part of the initial
contract.

The registry must answer:

- Is this adapter type known and compatible?
- Which configuration schema does it accept?
- Which event types can it emit?
- Can multiple listener configurations share one runtime instance?
- What is its impact descriptor before and after startup?
- Which capabilities or external commands does it require?

### Adapter Runtime

Each runtime instance has a stable key derived from the adapter type and the
portion of configuration that controls the underlying subscription. Several
listeners can be attached to one runtime.

Lifecycle:

```text
disabled -> preflight -> starting -> running
                         |            |
                         v            v
                       failed <---- degraded
                         ^            |
                         +-- stopping <-+
```

Adapters emit health transitions separately from domain events. A degraded
adapter may continue delivering partial events if it declares that behavior.

### Event Normalizer

Transforms raw adapter observations into versioned immutable events. It:

- rejects oversized or structurally invalid payloads;
- assigns ID, sequence, observed time, origin, and root correlation;
- preserves source-provided occurrence time only when available;
- strips raw fields not included in the normalized contract;
- classifies provenance and sensitivity;
- validates emitted type against the adapter declaration.

### Event Queue

The initial design uses one bounded logical acceptance queue so event order is
well-defined. Implementation may use asynchronous I/O, but acceptance sequence
and policy evaluation order must remain deterministic.

Required behavior:

- configurable hard capacity;
- explicit overflow strategy by event class;
- critical diagnostics cannot recursively flood the same queue;
- queue depth and dropped/suppressed counters exposed to status;
- graceful shutdown drains or records abandonment according to policy;
- no unbounded promise, callback, or action accumulation.

### Policy Engine

Pure domain component: input is one immutable event, a validated policy
snapshot, an injectable clock, and an allowlisted context snapshot. Output is
an evaluation plan. The engine performs no direct I/O.

It owns:

- deterministic policy ordering;
- trigger and condition matching;
- group-key derivation;
- debounce, cooldown, and rate-limit state;
- terminal behavior;
- causal depth checks;
- an explainable evaluation trace;
- production of ordered action requests.

### Action Dispatcher

Resolves typed action requests to executors and applies concurrency, timeout,
and error behavior. Action execution is separate from policy evaluation so the
pure engine remains fixture-testable.

Every execution yields an Action Result. Raw stdout/stderr or exception text is
bounded and sanitized before retention or display.

### State and Journal Stores

Use narrow interfaces even if one backing format initially implements several:

- `ConfigurationStore`: candidate and last known-good revisions;
- `RuntimeStateStore`: debounce/cooldown, schedule, replace-key, and recovery
  state that must survive restart;
- `EventJournal`: optional bounded normalized events and evaluation summaries;
- `PayloadStore`: optional retained images or other bounded payloads.

Storage must not retain live QML/DBus objects.

### Diagnostics and Status

Provide structured status rather than requiring users to inspect shell logs:

- runtime/config revision;
- adapter and listener health;
- queue depth and overflow count;
- event accepted/suppressed/actioned counters;
- last policy match or validation failure;
- resource impact and live measurements;
- last action failure by safe code and summary;
- whether global pause is active.

## 5. Versioned Contracts

The following shapes establish semantics; exact serialization syntax is
confirmed during activation.

### Listener configuration

```json
{
  "schemaVersion": 1,
  "id": "downloads-watch",
  "name": "Downloads completed",
  "enabled": false,
  "adapter": {
    "type": "filesystem",
    "config": {
      "roots": ["/home/example/Downloads"],
      "recursive": false,
      "events": ["created", "modified", "moved", "removed"],
      "exclude": ["*.part", "*.tmp"]
    }
  },
  "retention": {
    "mode": "metadata",
    "maxAge": "7d"
  }
}
```

Enabling is a separate operation after validation and impact acknowledgement;
writing `enabled: true` cannot silently bypass a newly required warning.

### Event envelope

```json
{
  "schemaVersion": 1,
  "id": "019...",
  "sequence": 1842,
  "type": "media.track.changed",
  "occurredAt": null,
  "observedAt": "2026-10-02T14:45:12.318-04:00",
  "source": {
    "adapter": "media",
    "listenerId": "spotify-listener",
    "instance": "spotify"
  },
  "subject": {},
  "data": {},
  "provenance": "observed",
  "confidence": null,
  "sensitivity": "normal",
  "origin": "external",
  "correlationId": "019...",
  "causationId": null,
  "causalDepth": 0
}
```

Rules:

- `occurredAt` is nullable.
- `observedAt` is always assigned by the accepting runtime.
- `sequence` is locally monotonic within a runtime/state generation.
- `confidence` is absent/null unless the adapter can justify inference.
- `subject` identifies what changed; `data` describes the change.
- sensitive values use explicit typed fields so redaction is predictable.

### Policy configuration

```json
{
  "schemaVersion": 1,
  "id": "notify-spotify-track",
  "name": "Show Spotify track changes",
  "enabled": true,
  "priority": 100,
  "trigger": {
    "listenerIds": ["spotify-listener"],
    "eventTypes": ["media.track.changed"],
    "origins": ["external"]
  },
  "conditions": [
    {
      "field": "data.playbackStatus",
      "operator": "equals",
      "value": "playing"
    }
  ],
  "controls": {
    "groupBy": ["source.instance"],
    "debounce": "2s",
    "cooldown": "1s",
    "rateLimit": {"count": 20, "window": "1m"},
    "terminal": false
  },
  "onActionError": "continue",
  "actions": [
    {
      "type": "notification.show",
      "title": "{{data.title}}",
      "body": "{{data.artist}}",
      "replaceKey": "media:{{source.instance}}"
    }
  ]
}
```

Templates are not shell templates. They resolve only allowlisted scalar event
fields, have bounded output, and cannot evaluate expressions or call functions.

### Action result

```json
{
  "schemaVersion": 1,
  "actionId": "...",
  "eventId": "...",
  "policyId": "notify-spotify-track",
  "actionIndex": 0,
  "type": "notification.show",
  "status": "succeeded",
  "startedAt": "...",
  "finishedAt": "...",
  "code": "shown",
  "summary": "Notification accepted",
  "causedEventIds": []
}
```

Allowed statuses are `succeeded`, `failed`, `skipped`, `suppressed`, and
`timed-out`.

### Impact descriptor

```json
{
  "schemaVersion": 1,
  "listenerId": "downloads-watch",
  "model": "filesystem-watch",
  "resident": true,
  "sharedRuntime": true,
  "polling": false,
  "pollIntervalMs": null,
  "watchDescriptors": {
    "estimated": 842,
    "live": null,
    "systemLimit": 524288
  },
  "residentProcesses": 0,
  "maySpawnProcesses": false,
  "privileged": false,
  "dataAccess": ["path", "file-name", "event-type"],
  "capturesContent": false,
  "retention": "metadata-7d",
  "warnings": []
}
```

The runtime must not populate false precision. Unknown values remain null and
the UI labels them as unavailable.

## 6. Adapter Sharing and Reconciliation

Listener configuration is not runtime topology. The coordinator derives
topology:

```text
listeners
  -> validate adapter configurations
  -> compute compatible subscription groups
  -> derive one runtime key per group
  -> calculate impact
  -> reconcile old and new runtimes
```

Examples:

- Several media listeners share one MPRIS observation layer, then filter by
  player at listener dispatch.
- Several filesystem listeners share one `inotify` process but may require many
  kernel watch descriptors.
- Time listeners become durable schedule registrations rather than one shell
  timer object per listener.
- Hook listeners share one validated local ingress endpoint.

Disabling the last listener attached to a runtime must release that runtime's
resources after in-flight event handling reaches a safe boundary.

## 7. Policy Evaluation Semantics

### Ordering

1. Select enabled policies whose trigger accepts the event.
2. Sort by priority descending.
3. Break ties by stable policy ID ascending.
4. Evaluate conditions against one immutable context snapshot.
5. Apply controls using the injectable clock and group key.
6. Produce ordered action requests.
7. Stop after a terminal policy completes according to its error strategy.

### Conditions

Initial operators should be deliberately small and typed:

- equals / not-equals;
- one-of / not-one-of;
- exists / not-exists;
- numeric less-than / greater-than;
- string starts-with / ends-with / contains;
- optional bounded glob matching after security review.

No arbitrary JavaScript, QML, shell, or regular-expression evaluation belongs
in the initial condition language.

### Debounce

Debounce groups candidate events by the evaluated group key. The newest event
replaces the pending event until the quiet window elapses. The evaluation trace
records replaced event IDs.

### Cooldown

Cooldown begins after the relevant action set succeeds unless configuration
explicitly selects attempt-based cooldown. Suppressed events increment a
visible counter and may be journaled according to retention.

### Rate limit

Use a bounded rolling window per policy and group key. On overflow, suppress
actions and expose the count. Rate-limit diagnostics must not themselves create
an unbounded notification loop.

### Terminal policies

A terminal policy stops lower-order policies after its own actions and error
strategy finish. A terminal policy with no visible action can intentionally
suppress later outcomes while still leaving an evaluation trace.

## 8. Causality Model

### Required fields

- `origin`: external, omr, user, restored, or another defined source class;
- `correlationId`: root chain identity;
- `causationId`: immediate event or action that caused this event;
- `causalDepth`: incremented for derived events;
- action fingerprint: short-lived runtime key for reflected side effects.

### Guards

- Default maximum causal depth is an activation decision with a hard compiled
  ceiling.
- OmR-origin notifications are not reprocessed by Provider mode by default.
- Listener enable/disable actions are idempotent and do not emit redundant
  state events.
- Filesystem action fingerprints include canonical scope, operation, and a
  bounded time window; they never rely solely on filename.
- Media control actions may correlate the expected follow-up playback event but
  cannot assume every playback change was caused by OmR.

## 9. Adapter-Specific Architecture

### Time

The adapter owns schedule registration and reconciliation, while systemd is a
replaceable backend. Stable schedule IDs map to externally registered timers.
Startup compares configured schedules, durable OmR state, and backend state;
duplicates or orphans become diagnostics rather than silently firing.

The event should distinguish:

- scheduled time;
- actual observation/delivery time;
- lateness;
- missed-policy result;
- schedule occurrence identity for deduplication.

### Media

The adapter listens to MPRIS player membership and property changes. It keeps a
small in-memory snapshot per live player and produces stable track signatures
from available metadata. A short stabilization window prevents title, artist,
and artwork updates from becoming separate track-change events.

Player identity remains source-qualified and should not depend only on a
friendly display name.

### Hooks and explicit ingress

A small same-user ingress surface accepts an event type from an allowlist plus
strict structured fields. Hook shims translate positional Omarchy hook
arguments into that contract. Ingress:

- rejects unknown types and oversized payloads;
- uses literal argv when invoked from hook scripts;
- returns promptly;
- records unavailable runtime delivery according to a decided buffering policy;
- never allows the caller to inject arbitrary actions or policies.

### Filesystem and Trash

One watcher controller owns the subprocess/native watcher and distributes
normalized observations to listener scopes. It maintains:

- root-to-listener indexes;
- watch-descriptor accounting;
- recursive subdirectory registration;
- move-cookie correlation with expiry;
- exclude matching;
- root health and permission state;
- explicit overflow generation.

Trash handling parses only the metadata necessary to normalize Trash events.
Malformed metadata yields a degraded diagnostic rather than a fabricated
original path.

### Screenshot

Screenshot is a composite semantic adapter:

- explicit ingress from a cooperating command/hook has `explicit` provenance;
- configured output-directory observation has `observed` provenance;
- future heuristics use `inferred` provenance and require separate privacy
  review.

Duplicate explicit and observed events for the same output may be correlated
by canonical path, stable file identity where available, and a bounded time
window. The explicit event wins as the authoritative representation.

## 10. Action Architecture

Executors share a common contract:

```text
validate(action, capabilities) -> validation result
impact(action)                 -> execution/privacy impact
execute(request, context)      -> asynchronous Action Result
cancel(actionId)               -> bounded best-effort cancellation
```

### Notification

Companion dispatch should use the supported Omarchy notification command or
service surface with literal arguments. Stable `replaceKey` ownership is held
by OmR and translated to backend-specific replacement identity only at the
edge.

### OSD and sound

These remain distinct actions. Showing an OSD does not silently play sound,
and a sound failure does not rewrite notification semantics.

### Literal argv

Validation includes:

- non-empty command name not beginning with an option;
- string-only arguments;
- NUL rejection;
- per-argument and total-size bounds;
- explicit timeout and output cap;
- declared working directory policy;
- bounded concurrency;
- no shell interpolation.

The product must not imply that literal argv is harmless: it still executes as
the user and therefore requires clear policy ownership and preflight.

## 11. Persistence and Retention

### Configuration

Configuration needs human-inspectable versioning and transactional replacement.
Whether users primarily edit JSON/JSONC or use a UI remains open; both paths
must produce the same validated snapshot.

### Runtime state

Persist only state needed for correct recovery, such as:

- active configuration revision;
- durable schedule occurrence IDs;
- bounded cooldown/rate state if restart preservation is required;
- replace-key mappings that remain meaningful;
- global pause and acknowledgement revisions.

Do not persist transient object pointers, raw MPRIS objects, D-Bus actions, or
watch descriptors.

### Journal

The journal is optional per sensitivity/retention policy. It stores normalized
events and compact evaluation/action results, not raw adapter streams. It must
support:

- count/age/byte bounds;
- deterministic deletion;
- migration;
- pagination without loading the full history;
- removal of associated payloads;
- safe behavior on corruption or partial writes.

The exact backend is open. A future implementation should compare bounded
files and SQLite/helper approaches with measured memory and complexity.

## 12. Resource and Privacy Preflight

Preflight happens before changing live adapter topology. It compares the
current configuration to the candidate and reports deltas:

- adapters started/stopped;
- listener count;
- watch descriptors added/removed;
- resident or transient child processes;
- polling/wakeup behavior;
- privileges;
- newly observed data classes and paths;
- retention changes;
- measurement confidence.

Acknowledgement is tied to a stable impact fingerprint. Material scope or
impact changes invalidate the prior acknowledgement; cosmetic renames do not.

Memory presentation distinguishes:

- declared structural impact;
- measured total shell/helper PSS before and after controlled scenarios;
- unknown or shared attribution;
- current available memory.

It never reports a guessed exact listener allocation.

## 13. Local IPC and Trust Boundary

Any local IPC is a same-user convenience, not a remote API. It must:

- live under the user runtime directory or the scoped Omarchy shell IPC;
- validate method names, schemas, sizes, and event allowlists;
- reject caller-provided action definitions during event ingress;
- never accept shell source;
- avoid secrets in command-line arguments where process listings could expose
  them;
- return bounded structured responses;
- define behavior when the runtime is unavailable.

An external stable event-bus API is not part of the initial package.

## 14. UI Architecture

The initial UI should expose domain concepts rather than raw backend controls:

- listener list with adapter, scope, enabled state, and health;
- listener editor and preflight summary;
- policy list with priority, trigger, controls, and actions;
- synthetic-event policy test view;
- recent event/evaluation explanation view, subject to retention;
- diagnostics for queue, adapter, schedule, and action failures;
- global pause;
- explicit mode indicator showing Companion behavior.

Backend-specific details such as watch descriptors or systemd units appear in
an advanced diagnostics section, not as the primary mental model.

## 15. Failure and Recovery Model

| Failure | Required behavior |
| --- | --- |
| Invalid configuration | Reject candidate; retain last known-good revision. |
| Adapter unavailable | Mark failed/degraded; bounded reconnect; do not crash runtime. |
| Event queue full | Apply declared overflow strategy; count and surface loss. |
| Inotify overflow | Emit one bounded degradation signal; require/reconcile rescan. |
| Systemd timer discrepancy | Reconcile by stable schedule ID; never double-fire silently. |
| Notification action unavailable | Return failed action result; preserve event evaluation. |
| `exec.argv` timeout | Terminate within the declared strategy; truncate output; report timeout. |
| Journal corruption | Quarantine or stop journal writes safely; keep live engine behavior defined. |
| Shell restart | Rehydrate validated config/state; reconcile external sources; deduplicate. |
| Global pause | Stop side effects while retaining explicit health and configured state. |

Diagnostics must avoid creating recursive notification storms.

## 16. Verification Architecture

### Pure contract tests

- schema parsing and version rejection;
- migration fixtures;
- event normalization;
- condition operators and template resolution;
- deterministic policy order;
- debounce, cooldown, rate limit, and terminal semantics;
- causality and loop suppression;
- impact descriptor aggregation.

### Adapter fixture tests

- MPRIS partial metadata and player churn;
- schedule resume/restart/missed events;
- hook ingress validation and unavailable runtime;
- filesystem create/modify/move/remove, recursion, exclusions, overflow, and
  disappearing roots;
- Trash metadata variants;
- explicit/observed screenshot deduplication.

### Action tests

- argument validation and literal execution boundaries;
- timeouts, concurrency, output caps, and errors;
- notification replacement ownership;
- listener-state idempotence;
- action result serialization.

### Integration tiers

Report separately:

1. static/schema/lint results;
2. pure unit and fixture results;
3. local component integration;
4. read-only live source observation;
5. source-tree plugin smoke tests;
6. installed Companion plugin behavior;
7. future Provider takeover/rollback tests.

Passing one tier does not imply the later tiers passed.

### Resource scenarios

Measure at minimum:

- disabled installed plugin;
- enabled runtime with no listeners;
- one media listener;
- representative time schedules;
- small and large recursive filesystem scopes;
- burst events with and without retained history;
- UI closed and open;
- sustained idle CPU/wakeups;
- shutdown resource release.

Record environment, sample method, duration, median, and observed peak.

## 17. Provider-Mode Extension Point

Provider mode should reuse Listener/Event/Policy/Action contracts but add a
notification-server adapter and renderer boundary. It must not require changing
the meaning of existing Companion events.

The later package must decide:

- clone/routing relationship with `omarchy.notifications`;
- D-Bus name acquisition and release;
- incoming notification identity and replacement semantics;
- pass-through defaults;
- live action/inline reply lifetimes;
- DND, history, crash restore, image persistence, and popup UI;
- provider-specific memory/storage impact;
- pre-activation warning delivery before the provider is loaded;
- rollback to stock service.

## 18. Decisions Required Before Code Generation

The architecture is complete at the responsibility and behavior level. These
implementation choices remain deliberately open and are tracked in `todo.md`:

- final plugin ID;
- minimum Omarchy/Quickshell version;
- in-shell, companion, or hybrid runtime placement;
- configuration syntax and storage backend;
- UI surface for the first implementation slice;
- exact default limits and retention;
- event-ingress buffering while the runtime is unavailable;
- first vertical slice and its live-test boundary.

Code generation must not guess these choices. Activate the entry, record the
decisions, update `architect/PROJECT.md`, and then implement the phased plan.
