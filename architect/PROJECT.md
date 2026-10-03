# Project Adapter

## Project Identity

- projectName: OmR Notifications
- expandedName: Omarchy's Robust Notifications
- repository: `/home/uriak/Work/AppSource/com.github/omr-notifications`
- projectType: third-party Omarchy shell plugin with a Companion runtime
- primaryLanguages: Python 3.11+ and QML
- buildTools: Python standard library and unittest; no runtime dependencies
- testCommands: `PYTHONPATH=src python3 -m unittest discover -v`
- packageManager: none selected
- defaultBranch: `main`
- pluginId: `uriak.omr-notifications`

## Runtime / Framework Notes

- The initial product is an event-policy runtime, not a general desktop event
  bus and not a replacement notification daemon.
- Companion mode uses the stock Omarchy notification service. Provider mode is
  deferred and must be implemented as a separate capability package.
- A source adapter owns one shared subscription or watcher mechanism. Listener
  instances provide configuration and filtering without duplicating the
  underlying integration.
- The normalized flow is adapter -> listener -> event -> policy -> actions.
- A policy owns its trigger, contextual conditions, controls such as debounce
  and cooldown, and ordered actions.
- The core contract must remain independent from Quickshell object lifetimes,
  MPRIS object shapes, systemd unit output, and inotify wire details.
- Live integrations need explicit lifecycle states: disabled, preflight,
  starting, running, degraded, failed, and stopping.
- Configuration reload is transactional. A failed parse or validation cannot
  partially replace the live listener/policy graph.
- Event and action chains carry causal metadata and a bounded depth to prevent
  self-triggering automation loops.

## Responsibility Map

| Area | Responsibility |
| --- | --- |
| `core` | Versioned models, validation, event sequencing, queueing, policy evaluation, causality, diagnostics |
| `adapters` | Shared integrations and normalized event production |
| `actions` | Typed, bounded side effects and result reporting |
| `persistence` | Versioned configuration, last known-good state, journal/retention boundary |
| `ui` | Listener setup, policy editing, impact preflight, runtime status, diagnostics |
| `ipc` | Validated local event ingress and control surface |
| `companion` | Optional activation, systemd, or measurement helpers only when approved |

The path names are a planned ownership model. Implementation may refine them
after activation without collapsing the responsibility boundaries.

## XDG Ownership

The implemented separation is:

- configuration: `${XDG_CONFIG_HOME:-$HOME/.config}/omr-notifications/`;
- durable state/history: `${XDG_STATE_HOME:-$HOME/.local/state}/omr-notifications/`;
- regeneratable cache: `${XDG_CACHE_HOME:-$HOME/.cache}/omr-notifications/`;
- sockets and transient coordination: `${XDG_RUNTIME_DIR}/omr-notifications/`.

Plugin source/install files must not double as mutable runtime storage. Exact
filenames and the journal backend remain pending decisions.

## Verification Commands

For the source implementation:

```bash
PYTHONPATH=src python3 -m unittest discover -v
python3 -m compileall -q src tests
python3 bin/omr-notifications config validate examples/config.example.json
python3 bin/omr-notifications preflight examples/config.example.json
find . -name '*.json' -not -path './.git/*' -print0 | xargs -0 -n1 python3 -m json.tool >/dev/null
git diff --check
git status --short --branch
```

## Agent Boundaries

- shouldNotTouch: `/usr/share/omarchy`, installed plugins, shell configuration,
  user hooks, user systemd units, package state, notification service ownership,
  or real personal event history without explicit authorization
- generatedFiles: runtime configuration snapshots, event journals, images,
  caches, coverage, build output, and activation evidence must not be committed
- externalDependencies: Omarchy shell/Quickshell, FreeDesktop notifications,
  MPRIS, systemd user manager, and inotify are planned interfaces; exact
  compatibility baselines are not yet pinned
- securitySensitiveAreas: local event ingress, command actions, filesystem
  paths, notification content, provider takeover, configuration migration,
  action causality, and retained history

## Project-Specific Architect Rules

- Pending records are planning-only and never authorize implementation or host
  integration.
- Record any change to event semantics, policy ordering, action safety,
  provider scope, persistence, privacy defaults, or resource-warning behavior
  in the active Architect entry before code changes.
- Keep Provider mode out of the first implementation package.
- Keep factual observations distinct from inferred events throughout schemas,
  user interfaces, persistence, and tests.
- Never describe a path removal as destruction of the underlying file unless
  the source can establish that fact.
- Keep activation impact descriptors machine-readable and derived from actual
  listener configuration where possible.
