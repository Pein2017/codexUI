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

### Requirement: Domain modules SHALL depend on scoped gateway surfaces
Each state domain SHALL consume only the RPC and gateway capabilities it owns.

#### Scenario: Thread runtime state imports thread-focused gateway functions
- **WHEN** thread runtime logic needs to load messages, start turns, or interrupt turns
- **THEN** it SHALL depend on a thread-focused gateway surface
- **AND** it SHALL not import account, review, skills, and workspace APIs as part of the same broad dependency bag

#### Scenario: Workspace state imports workspace-focused gateway functions
- **WHEN** workspace root or local directory flows change
- **THEN** those state modules SHALL update against a workspace-focused gateway surface without affecting unrelated thread runtime imports
