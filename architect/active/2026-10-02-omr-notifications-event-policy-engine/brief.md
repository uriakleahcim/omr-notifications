# OmR Notifications Event-Policy Engine

## Original Request

Create an Omarchy plugin called **OmR Notifications**, short for **Omarchy's
Robust Notifications**. Its primary purpose is to observe selected desktop
events, decide whether they merit a notification or another response, and
execute the selected action without consuming unbounded memory.

Example event sources include:

- a command or reminder at a specified time;
- media track or playback changes;
- a screenshot being taken;
- a file or directory entry being removed;
- existing Omarchy lifecycle hooks;
- eventually, incoming desktop notifications.

## Product Statement

OmR Notifications is Omarchy's event-driven notification and automation policy
engine. It turns explicitly enabled event sources into normalized, explainable
events and runs deterministic, bounded policies over them.

Notifications are one action, not the entire architecture.

## Goal

Provide a coherent foundation in which users can:

1. enable a listener with a clear scope and resource/privacy preflight;
2. understand which normalized events that listener may produce;
3. attach deterministic policies to those events;
4. display, suppress, delay, group, record, or act on them;
5. diagnose missed, degraded, rate-limited, or failed behavior;
6. disable everything cleanly without leaving hidden background work.

## Initial Scope

- Companion mode using Omarchy's existing notification service.
- Versioned Listener, Event, Policy, Action, and Impact Descriptor contracts.
- Time, media, Omarchy hook, scoped filesystem, Trash, and screenshot event
  families.
- Notification, OSD, sound, literal argv, listener-state, and event-recording
  actions.
- Deterministic ordering, debounce, cooldown, grouping, rate limits, and
  terminal policies.
- Causality tracking and loop prevention.
- Transactional configuration reload and last known-good recovery.
- Bounded local state, privacy classification, and resource preflight.

## Deferred Scope

Provider mode is intentionally deferred. It would own the FreeDesktop
notification service, replace `omarchy.notifications`, and filter notifications
from unrelated applications. That work requires stock behavioral parity,
D-Bus ownership, live action lifetime, notification replacement semantics,
transactional activation, and rollback.

## Non-Goals

- a general-purpose cross-process desktop event bus;
- privileged or exhaustive filesystem auditing;
- eBPF, fanotify, or process-wide surveillance;
- remote telemetry, cloud rules, or multi-device synchronization;
- claims that inferred events are authoritative;
- unbounded history, images, queues, retries, or watch scopes;
- unrestricted shell evaluation;
- implementation, installation, or desktop activation during this pending
  planning phase.

## Status

Pending. The repository contains documentation and Architect records only.
Implementation requires explicit activation of this package.
