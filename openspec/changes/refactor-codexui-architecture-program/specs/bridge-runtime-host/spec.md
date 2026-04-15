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

### Requirement: Bridge hosting SHALL preserve one authoritative runtime notification contract
Notification delivery semantics for WebSocket readiness, fallback behavior, and event serialization SHALL remain consistent across supported hosts.

#### Scenario: WebSocket readiness is emitted consistently
- **WHEN** a browser connects to the bridge WebSocket endpoint
- **THEN** both development and production hosts SHALL emit the same ready notification contract before streaming subsequent bridge notifications

#### Scenario: Notification subscribers receive the same event payload shape
- **WHEN** the bridge forwards a Codex app-server notification
- **THEN** the frontend SHALL observe the same serialized notification shape regardless of which host implementation is serving the UI

### Requirement: Server host code SHALL be organized by capability-oriented route modules
The server host SHALL expose bridge, auth, local browse, and feature-specific routes through capability-oriented registration seams.

#### Scenario: Host entrypoints compose route modules instead of owning all handlers inline
- **WHEN** a new server-backed feature is added
- **THEN** the host entrypoint SHALL compose an explicit route-registration module for that capability
- **AND** the host entrypoint SHALL not grow by inlining unrelated route implementations
