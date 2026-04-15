## ADDED Requirements

### Requirement: Desktop state SHALL be partitioned into explicit domain modules
Desktop application state SHALL be organized into modules with declared ownership boundaries instead of concentrating unrelated concerns in one monolithic state implementation.

#### Scenario: Thread index concerns are isolated from live runtime concerns
- **WHEN** developers update project grouping, read state, or thread ordering behavior
- **THEN** those changes SHALL live in a thread index domain module
- **AND** they SHALL not require editing live runtime event ingestion or conversation rendering state in the same module

#### Scenario: Workspace and new-thread flows are isolated from conversation state
- **WHEN** developers update folder picking, worktree creation, or workspace root persistence
- **THEN** those changes SHALL be owned by a workspace domain module rather than by the conversation or live timeline domain

#### Scenario: Bridge/session control is isolated from thread content state
- **WHEN** developers update notification stream lifecycle, bridge recovery, pending server requests, or server-request responses
- **THEN** those changes SHALL be owned by a bridge/session-control domain
- **AND** they SHALL not be modeled as incidental state inside thread runtime or workspace domains

#### Scenario: Session capabilities are isolated from thread/workspace ownership
- **WHEN** developers update skills catalogs, account/quota snapshots, model catalogs, or other session-wide capability state
- **THEN** those changes SHALL be owned by a session-capabilities domain
- **AND** they SHALL not be mixed into thread-only or workspace-only state modules

### Requirement: A stable desktop-state façade SHALL preserve incremental migration
The architecture SHALL provide a compatibility façade so components can migrate to domain state incrementally without forcing a flag day rewrite.

#### Scenario: Existing consumers migrate without a one-shot rewrite
- **WHEN** domain modules are introduced
- **THEN** the root desktop-state API SHALL continue to expose the selectors and actions needed by current consumers during migration
- **AND** internal implementation MAY delegate to multiple domain modules behind that façade

#### Scenario: New features bind to domain APIs first
- **WHEN** a new feature needs desktop state
- **THEN** it SHALL depend on the smallest relevant domain API or façade selector
- **AND** it SHALL not read unrelated refs from a monolithic catch-all object

#### Scenario: The migration façade does not become a new permanent monolith
- **WHEN** migration phases introduce new domain-owned state or actions
- **THEN** the compatibility façade SHALL not add new cross-domain exports unless compatibility requires them
- **AND** each migration phase SHALL reduce or at least not increase the façade export surface

#### Scenario: Consumers stop bypassing the migration façade and narrow seams
- **WHEN** page or feature components migrate to domain modules
- **THEN** they SHALL stop importing broad catch-all gateway surfaces or broad notification subscriptions when narrower seams exist
- **AND** any remaining exceptions SHALL be explicit and temporary

### Requirement: Runtime event ownership SHALL be explicit before state is projected into the UI
Notification parsing, normalization, and ownership routing SHALL be defined before events are stored in state domains or projected into the conversation timeline.

#### Scenario: Notification methods map to explicit owners
- **WHEN** the bridge receives a runtime notification
- **THEN** the system SHALL route that notification to an explicit owning domain or adapter
- **AND** the implementation SHALL not rely on one catch-all reducer to interpret unrelated event families

#### Scenario: Payload normalization occurs before domain state updates
- **WHEN** runtime payloads such as token usage, quota snapshots, server requests, or live deltas are consumed
- **THEN** normalization SHALL happen in a gateway/adapter seam before domain state is updated
- **AND** domain modules SHALL consume normalized events rather than re-parsing raw bridge payloads independently

### Requirement: Domain modules SHALL depend on scoped gateway surfaces
Each state domain SHALL consume only the RPC and gateway capabilities it owns.

#### Scenario: Thread runtime state imports thread-focused gateway functions
- **WHEN** thread runtime logic needs to load messages, start turns, or interrupt turns
- **THEN** it SHALL depend on a thread-focused gateway surface
- **AND** it SHALL not import account, review, skills, and workspace APIs as part of the same broad dependency bag

#### Scenario: Workspace state imports workspace-focused gateway functions
- **WHEN** workspace root or local directory flows change
- **THEN** those state modules SHALL update against a workspace-focused gateway surface without affecting unrelated thread runtime imports

#### Scenario: Gateway seams cover the actual control planes they own
- **WHEN** domain modules are introduced for bridge/session-control, session-capabilities, or composer attachment flows
- **THEN** the gateway layer SHALL expose corresponding scoped seams such as bridge notifications, server requests, accounts/quota, or composer/local-file capabilities
- **AND** those capabilities SHALL not remain in a miscellaneous catch-all gateway surface
