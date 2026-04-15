## ADDED Requirements

### Requirement: Development and production hosts SHALL share one canonical bridge registration model
Bridge route registration and bridge-backed local-file endpoints SHALL be defined once and reused by both the Vite development host and the production Express server.

#### Scenario: Shared bridge endpoints exist across hosts
- **WHEN** the application runs in development or production mode
- **THEN** `/codex-api/*`, `/codex-api/ws`, and supported local-file endpoints SHALL be registered from shared bridge-host code
- **AND** the endpoint behavior SHALL not depend on duplicated ad hoc implementations in each host entrypoint

#### Scenario: Local-file features do not drift across environments
- **WHEN** a local image, local file, local directory, or local editor route is added or modified
- **THEN** the same capability SHALL be available in both development and production hosts without requiring duplicated edits

#### Scenario: Canonical host route inventory is explicit
- **WHEN** the bridge/runtime host contract is implemented
- **THEN** the canonical surface SHALL explicitly include `/codex-api/rpc`, `/codex-api/meta/methods`, `/codex-api/meta/notifications`, `/codex-api/server-requests/respond`, `/codex-api/server-requests/pending`, `/codex-api/events`, `/codex-api/ws`, `/codex-local-image`, `/codex-local-file`, `/codex-local-directories`, `/codex-local-open/*path`, `/codex-local-browse/*path`, and `/codex-local-edit/*path`
- **AND** hosts SHALL not silently omit any route from that inventory without an explicit contract update

### Requirement: Bridge hosting SHALL preserve one authoritative transport contract
Notification delivery semantics for WebSocket readiness, SSE fallback, auth-wrapped upgrades, and event serialization SHALL remain consistent across supported hosts.

#### Scenario: WebSocket readiness is emitted consistently
- **WHEN** a browser connects to the bridge WebSocket endpoint
- **THEN** both development and production hosts SHALL emit the same ready notification contract before streaming subsequent bridge notifications

#### Scenario: Notification subscribers receive the same event payload shape
- **WHEN** the bridge forwards a Codex app-server notification
- **THEN** the frontend SHALL observe the same serialized notification shape regardless of which host implementation is serving the UI

#### Scenario: SSE fallback remains part of the runtime contract
- **WHEN** WebSocket transport is unavailable or the client falls back to `/codex-api/events`
- **THEN** both hosts SHALL emit the same ready-first semantics and compatible event payload shapes
- **AND** SSE keepalive behavior SHALL remain sufficient for long-lived local sessions

#### Scenario: Auth-wrapped upgrades use one canonical policy when auth is enabled
- **WHEN** the production host enables auth for bridge traffic
- **THEN** WebSocket upgrade authorization and unauthorized-close behavior SHALL be centralized rather than reimplemented per host
- **AND** development MAY omit auth while still using the same shared host modules

### Requirement: Local-file routes SHALL preserve HTTP semantics parity
Local-file route behavior SHALL match across development and production not only by path presence, but also by response semantics.

#### Scenario: Local-file headers and errors remain consistent
- **WHEN** local-file, local-browse, local-open, or local-edit routes return success or failure responses
- **THEN** status codes, JSON error shapes, cache headers, content-disposition behavior, and text-editor semantics SHALL remain materially consistent across hosts

#### Scenario: Editable local-file writes preserve request limits and failure behavior
- **WHEN** the host handles `PUT /codex-local-edit/*path`
- **THEN** body-size limits and failure semantics SHALL not diverge materially between development and production hosts

### Requirement: Server host code SHALL be organized by capability-oriented route modules
The server host SHALL expose bridge, auth, local browse, and feature-specific routes through capability-oriented registration seams.

#### Scenario: Host entrypoints compose route modules instead of owning all handlers inline
- **WHEN** a new server-backed feature is added
- **THEN** the host entrypoint SHALL compose an explicit route-registration module for that capability
- **AND** the host entrypoint SHALL not grow by inlining unrelated route implementations
