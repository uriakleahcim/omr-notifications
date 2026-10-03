# Product Requirements

## Core Outcome

A user can configure a bounded desktop event source, see its resource and
privacy impact before enabling it, and decide through deterministic policies
whether the resulting events should notify, display an OSD, play a sound,
execute a literal command, change listener state, or be recorded silently.

The system must explain what it observed, how certain that observation was,
which policy matched, which controls suppressed or delayed execution, and what
each action did.

## Users and Primary Jobs

### Desktop user

- Create reminders and recurring schedules that survive shell restarts.
- Receive useful media, screenshot, Trash, or filesystem notifications without
  repeated noise.
- Limit observation to intentional sources and paths.
- Understand resource, privacy, and execution consequences before activation.
- Pause, disable, inspect, and remove listeners without residual background
  activity.

### Rule author

- Match stable normalized event fields instead of implementation-specific raw
  output.
- Combine source filters with session context and deterministic controls.
- Test a policy against fixtures before applying it live.
- Diagnose why an event did or did not execute an action.

### Maintainer or code-generation agent

- Implement adapters without coupling their raw API to the policy engine.
- Extend event and action types through versioned schemas.
- Verify pure policy behavior without running a live Omarchy desktop.
- Distinguish source tests, installed-plugin tests, and host integration tests.

## Public Concepts

### Listener

A listener is versioned user configuration with:

- stable ID and display name;
- adapter type and adapter-specific configuration;
- enabled state;
- expected event types;
- sensitivity and retention overrides;
- an activation impact descriptor;
- current lifecycle and health state.

Multiple listeners may share one source adapter connection.

### Event

An event is immutable after acceptance into the engine. Required semantics:

- schema version;
- globally unique event ID;
- monotonically assigned local sequence;
- stable event type;
- optional source-reported `occurredAt`;
- engine-assigned `observedAt`;
- adapter and listener identity;
- structured subject and data objects;
- provenance and optional inference confidence;
- sensitivity classification;
- origin, correlation, causation, and causal depth.

Raw source payloads must not be retained by default when normalized fields are
sufficient.

### Policy

A policy contains:

- stable ID, name, enabled state, and integer priority;
- a trigger selecting listener IDs and exact event types;
- typed conditions over normalized fields and permitted context;
- controls for debounce, cooldown, grouping, rate limits, and termination;
- ordered actions;
- explicit action-error behavior.

Policy order is deterministic: descending priority, then stable policy ID. All
matching policies run unless a matched policy is terminal or an explicit
error strategy stops the event.

### Action

Each action receives the immutable event plus a read-only evaluated policy
context. It returns a structured result with status, timestamps, safe summary,
and error code. Action implementations must not mutate the event.

## Modes

### Companion mode requirements

- Use Omarchy's active notification service rather than owning the FreeDesktop
  notification name.
- Process only OmR listener events and explicitly submitted local ingress
  events.
- Do not claim to filter or suppress notifications from unrelated applications.
- Remain usable when Provider mode has never been installed or configured.

### Provider mode requirements

Deferred to a separate package. The later package must preserve Companion
behavior and additionally specify:

- single-owner notification-server takeover;
- parity with current Omarchy popup, DND, persistence, replacement, action, and
  history behavior;
- pass-through defaults for unmatched application notifications;
- live action and inline-reply lifetime;
- provider health checks;
- atomic stock-service disable/OmR enable transition;
- rollback on load, ownership, IPC, or rendering failure;
- explicit privacy and memory warning before takeover.

## Initial Source Adapters

### Time adapter

Event families:

- `time.at.fired`;
- `time.after.fired`;
- `time.schedule.fired`;
- `time.schedule.missed`;
- `time.schedule.failed`.

Requirements:

- represent timestamps with timezone information;
- distinguish relative duration from recurring schedule;
- define whether suspend time counts for relative schedules;
- define missed policies: ignore, fire-on-resume, record-missed, or reschedule;
- survive shell restart where configured;
- avoid one permanently resident QML timer per schedule;
- reconcile external timer state at startup;
- prevent duplicate fire after restart or delayed delivery.

### Media adapter

Event families:

- `media.player.appeared` and `media.player.disappeared`;
- `media.track.changed`;
- `media.playback.changed`;
- `media.active-player.changed`.

Requirements:

- use event-driven MPRIS observation rather than polling;
- normalize player identity, title, artist, album, art reference, and playback
  state when available;
- tolerate absent or misleading metadata;
- stabilize piecemeal property updates before emitting track changes;
- deduplicate equivalent track signatures;
- avoid persisting artwork or media text unless retention explicitly allows it.

### Omarchy hook adapter

Event families mirror explicitly supported hooks, such as:

- `omarchy.hook.post-boot`;
- `omarchy.hook.post-update`;
- `omarchy.hook.theme-set`;
- `omarchy.hook.font-set`;
- `omarchy.hook.battery-low`.

Requirements:

- receive explicit, schema-validated local ingress;
- install only user-owned hook scripts and only after authorization;
- remain safe when a hook fires while the shell or OmR service is unavailable;
- bound retry and never block the originating Omarchy operation indefinitely;
- preserve exact hook arguments only when required by the normalized event.

### Filesystem adapter

Event families:

- `filesystem.entry.created`;
- `filesystem.entry.modified`;
- `filesystem.entry.removed`;
- `filesystem.entry.moved`;
- `filesystem.watch.degraded`;
- `filesystem.watch.overflow`.

Requirements:

- accept only explicit path roots;
- display the resolved scope and data classes before activation;
- consolidate roots into one watcher mechanism where practical;
- correlate move cookies when available;
- add watches for new subdirectories in recursive mode;
- surface path disappearance, permission failure, watch-limit exhaustion, and
  queue overflow;
- support exclude patterns without following unexpected symlink escapes;
- never claim an entry removal proves destruction of underlying storage;
- not read file contents in the initial package.

### Trash adapter

Event families:

- `trash.item.added`;
- `trash.item.restored` where reliably observable;
- `trash.item.removed` where reliably observable;
- `trash.watch.degraded`.

Requirements:

- use FreeDesktop Trash metadata when available;
- treat original paths and deletion timestamps as sensitive;
- distinguish movement into Trash from permanent destruction;
- reuse the consolidated filesystem machinery rather than spawning a separate
  watcher per listener.

### Screenshot adapter

Event families:

- `screenshot.created` for explicit or authoritative observations;
- `screenshot.detected` for heuristic inference;
- `screenshot.failed` for explicit cooperating producers.

Requirements:

- prefer an explicit ingress command or future Omarchy hook;
- allow an observed configured-directory fallback;
- label source provenance visibly;
- never claim clipboard image inference is authoritative;
- keep clipboard-content inspection out of the initial scope;
- avoid modifying packaged Omarchy screenshot commands.

## Initial Actions

### `notification.show`

- title, body, urgency, timeout, icon/glyph, image reference, and stable
  `replaceKey` where supported;
- structured templates may access allowlisted normalized fields only;
- action-generated notifications carry an OmR origin marker;
- image paths must obey configured roots and size limits.

### `notification.dismiss`

- may target only a logical notification handle or replace key created and
  owned by OmR;
- must not expose or reuse stale provider notification IDs.

### `osd.show`

- short, bounded message and known icon key;
- may fall back to notification only when the policy requests fallback.

### `sound.play`

- explicit asset or allowlisted path;
- bounded duration and concurrency;
- no implicit shell command construction.

### `exec.argv`

- non-empty string array with bounded argument and total size;
- no shell interpretation, variable interpolation, or command substitution;
- explicit timeout, concurrency limit, and safe result truncation;
- environment inheritance and working-directory behavior must be documented;
- failures become action results rather than crashing the engine.

### `listener.enable` and `listener.disable`

- target a known listener ID;
- create causal events with bounded depth;
- cannot bypass resource preflight for a listener whose impact changed;
- must remain idempotent.

### `event.record`

- write the normalized event and selected evaluation metadata only;
- obey sensitivity and retention policy;
- remain bounded and deletable.

## Policy Controls

- **Debounce:** wait for a quiet window within a grouping key and process the
  newest relevant event.
- **Cooldown:** suppress repeated actions for a grouping key after successful
  execution.
- **Group:** derive a stable key from allowlisted event field paths.
- **Rate limit:** bound executions in a time window; expose suppressed counts.
- **Terminal:** stop evaluation of lower-order policies after the current
  policy's action/error behavior completes.
- **Error strategy:** continue, stop-policy, or stop-event. Default is continue
  with a recorded failure.

Controls must use an injectable clock in tests.

## Causality and Loop Prevention

- Root events set `correlationId` to their own ID.
- Derived events retain the correlation ID and name the parent event or action
  as `causationId`.
- Causal depth is bounded; exceeding it suppresses further side effects and
  records a diagnostic.
- OmR-generated notifications are ignored by a future Provider listener unless
  a policy explicitly opts into self-origin events.
- Recent action fingerprints suppress immediate reflection from filesystem,
  media, and listener-state adapters.
- Loop suppression must be explainable in diagnostics and testable with
  deterministic fixtures.

## Resource Preflight

Every adapter must produce a machine-readable impact descriptor based on the
candidate listener configuration. It should include where applicable:

- resident versus transient behavior;
- shared runtime status;
- polling and interval;
- estimated and live watch descriptor count;
- resident child-process count;
- possible transient process spawning;
- privilege requirement;
- observed data classes such as names, paths, metadata, or content;
- persistence and retention behavior;
- current system limit and whether the candidate approaches it;
- measured baseline reference when one exists.

Activation must require acknowledgement when the scope, privacy class,
privilege, polling, or measured resource tier crosses configured thresholds.
Warnings are derived from descriptors rather than hardcoded per-listener prose.

Exact per-listener RAM is not a requirement when running inside the shared
shell process. Controlled before/after PSS measurements may be reported as an
observed process-level delta with test conditions.

## Configuration and Persistence

- All persisted formats are versioned.
- Parse and validate a candidate configuration completely before activation.
- Retain a last known-good configuration and report rejected revisions.
- Do not mix plugin installation files with mutable settings or state.
- Use XDG config/state/cache/runtime locations.
- Journal and history retention must be bounded by count, age, and/or bytes.
- Deletion must remove associated retained payloads and derived indexes.
- Migrations must be forward-tested and failure-safe.
- The initial persistence backend remains an activation decision behind a
  narrow store interface.

## User Experience Requirements

- Create, inspect, enable, disable, and delete listeners.
- Preview expected event types and resource/privacy impact before enabling.
- Create and test policies against synthetic fixture events.
- Show listener lifecycle and degraded states.
- Explain policy matches, control suppression, loop suppression, and action
  results without requiring raw logs.
- Provide a global pause that prevents side effects without destroying
  configuration.
- Make Companion versus Provider capability boundaries explicit.
- Never imply OmR can prove a person read a notification or that a removed path
  means physical data destruction.

## Security and Privacy Requirements

- Local-only operation by default; no telemetry.
- Same-user local ingress with strict schema and size validation.
- Minimum normalized metadata and explicit retention.
- Sensitive fields redacted in ordinary logs and diagnostics.
- No generic shell evaluation in the initial package.
- Path access remains within configured scopes.
- Actions, listener state changes, and configuration revisions are auditable
  without storing secrets.
- History export, if later added, is opt-in and labeled sensitive.

## Reliability Requirements

- Bounded serialized event acceptance with an explicit overflow strategy.
- Adapter reconnect with bounded exponential backoff and visible state.
- Idempotent reconciliation after shell restart.
- No partial configuration activation.
- No stale live object references in durable event or history models.
- Safe behavior when systemd, MPRIS, inotify, an Omarchy hook, or the
  notification action target is unavailable.
- Disabling a listener releases its adapter reference and associated resources
  when no other listener requires them.

## Acceptance Criteria for the Initial Package

- Versioned schemas exist for listeners, events, policies, actions, action
  results, and impact descriptors.
- Fixture-driven tests prove deterministic ordering, conditions, controls,
  action error handling, causality, and loop suppression.
- Time, media, hook, scoped filesystem, Trash, and screenshot adapters meet
  their declared lifecycle and degradation behavior.
- Companion-mode notification, OSD, sound, argv, listener-state, and record
  actions pass source and integration tests.
- Invalid configuration leaves the prior live configuration active.
- Resource preflight shows actual configured watch scope and data capture.
- Queues, journals, images, subprocesses, and retries have tested bounds.
- Live desktop tests are reported separately from fixture tests.
- No Provider-mode takeover exists in the initial resolved package.
