# Context

## Why This Is an Event-Policy Engine

The original idea was to track events and decide whether they should produce a
notification. Once time schedules, media changes, screenshot creation,
filesystem observations, and Omarchy hooks are all first-class sources, a
notification-only abstraction becomes misleading. The stable architecture is:

```text
Listener -> Event -> Policy -> Action
```

A notification is one output. The same event may be ignored, recorded, grouped,
delayed, shown as an OSD, paired with sound, or used to execute a literal argv
action.

## Listener Versus Trigger

Subscription and semantic matching are separate concerns. A media adapter can
hold one MPRIS subscription while emitting several event types. Listener
configuration scopes that subscription. A policy trigger then selects event
types and listener IDs.

This separation prevents one connection or process per semantic rule and makes
resource preflight meaningful.

## Companion Versus Provider

Companion mode generates outcomes from OmR-controlled event sources and uses
the existing Omarchy notification service. It is additive and suitable for the
first implementation.

Provider mode would own the desktop notification service and could filter
unrelated application notifications. This is qualitatively different because
it must preserve notification IDs, replacement behavior, actions, replies,
DND, popup UI, persistence, and failure recovery. A failed takeover could leave
the user without notifications. It is therefore deferred.

## Current Omarchy Integration Observations

The local installed Omarchy 4.0.4-1 tree inspected during planning showed:

- the long-running `omarchy-shell` Quickshell process loads enabled service
  plugins;
- first-party `omarchy.notifications` is a keep-loaded notification service;
- first-party `omarchy.media` provides MPRIS state and control;
- third-party plugins use user-owned plugin directories and cannot claim the
  reserved `omarchy.*` namespace;
- first-party non-bar services are enabled differently from third-party
  services;
- generic plugin enable does not provide a standard manifest-level resource or
  replacement warning;
- plugins run unsandboxed in the user's shell process;
- current reminders use transient user systemd timers;
- current documented hooks include post-boot, post-update, theme-set, font-set,
  and battery-low;
- screenshot flows can create notifications, files, or clipboard data, but no
  dedicated documented screenshot hook was found.

Implementation must recheck these facts because Omarchy is actively developed.
Packaged files under `/usr/share/omarchy` are reference material only and must
not be edited.

## Event Time and Provenance

`occurredAt` and `observedAt` solve different problems. An external timer may
have been scheduled for an earlier instant but observed only after resume. A
filesystem watcher reports observation time but usually not an independent
source occurrence time. OmR must preserve this distinction rather than
backdating events.

Provenance further distinguishes:

- explicit cooperating producers;
- direct observations from an authoritative interface;
- inferred heuristics.

Confidence is useful for inference but should not create false precision for
direct observations.

## Filesystem Precision

From one watched directory's perspective, an entry can disappear because it
was removed, renamed, or moved elsewhere. OmR should report namespace facts it
can support. Movement to FreeDesktop Trash is semantically different from
permanent destruction and may provide separate metadata such as original path
and deletion time.

Global deletion auditing would require much broader and potentially privileged
mechanisms. It is not an initial goal.

## Screenshot Precision

A future explicit screenshot hook or cooperating wrapper can produce an
authoritative event. Watching a configured output directory produces a direct
file observation, not proof of which program created it. Clipboard-image
heuristics are weaker and more privacy-sensitive. Provenance keeps these paths
from being presented as equivalent.

## Resource Warning Philosophy

The user specifically wants memory/resource consequences considered when a
listener is activated. Because shell plugins share a process, exact listener
RAM ownership is usually unavailable. OmR should instead combine:

- declarative structural impact from the adapter;
- live configuration-derived counts and scopes;
- system limits such as available watch descriptors;
- measured process-level deltas from controlled scenarios;
- privacy and retention consequences.

Warnings should say what is known, shared, measured, estimated, or unavailable.

## Why Causality Is a Core Contract

Automation side effects frequently resemble new input events. An executed
command may create a watched file, a media control changes playback state, a
listener-state action emits state, and future Provider notifications may see
OmR's own notification. Without correlation, causation, depth, origin, and
fingerprint guards, seemingly simple policies can form invisible loops.

Loop prevention belongs in the event and action contracts, not as a later UI
patch.

## Original Planning Boundary

This repository began as a documentation-only local scaffold. On 2026-10-03,
the user explicitly activated a source-only Companion implementation. The
plugin manifest, QML host, Python runtime, contracts, examples, and tests now
exist in the repository. No live plugin, hook, timer, systemd unit, desktop
setting, remote, or commit was created by that implementation run.
