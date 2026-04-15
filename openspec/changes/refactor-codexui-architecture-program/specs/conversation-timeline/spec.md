## ADDED Requirements

### Requirement: Conversation rendering SHALL be driven by one deterministic timeline model
The thread view SHALL be built from a canonical timeline model that merges persisted thread snapshots and live runtime events into one chronological stream.

#### Scenario: Tool activity interleaves with assistant text in chronological order
- **WHEN** a turn alternates between assistant text, command execution, MCP activity, or file changes
- **THEN** the conversation timeline SHALL render those rows in arrival order
- **AND** the UI SHALL not split assistant text into one top block and tool activity into a trailing bottom stack

#### Scenario: Persisted snapshots reconcile live rows deterministically
- **WHEN** a silent thread refresh loads authoritative persisted messages during or after a turn
- **THEN** the timeline builder SHALL reconcile duplicate live rows against the persisted snapshot without changing the semantic order of the conversation

#### Scenario: Canonical ordering keys exist across persisted, live, and synthetic rows
- **WHEN** the timeline builder emits rows
- **THEN** each row SHALL carry a canonical ordering contract including a stable `rowId`, `rowKind`, `orderKey`, and `sourceMessageIds`
- **AND** persisted rows, live rows, and synthetic aggregate rows SHALL participate in one deterministic ordering scheme

#### Scenario: Reconciliation covers late metadata and segmented live output
- **WHEN** live assistant segments, command/file-change deltas, or turn metadata arrive before authoritative persisted data
- **THEN** the builder SHALL define how segmented live rows are merged, rebound, or replaced when persisted data arrives
- **AND** late `turnId` or `turnIndex` metadata SHALL not force unrelated rows to be reinterpreted

### Requirement: Conversation row modeling SHALL be separated from row rendering
The system SHALL represent rendered conversation rows as typed view models that are computed before Vue templates render them.

#### Scenario: Distinct row types map to dedicated renderers
- **WHEN** the thread contains assistant text, live stages, command rows, MCP rows, or file changes
- **THEN** the conversation view SHALL map them into distinct row model types
- **AND** each row type SHALL be rendered by dedicated row-oriented components or render branches with clear ownership

#### Scenario: Adding a new live runtime row type does not require rewriting the entire thread view
- **WHEN** a future feature introduces a new runtime event row
- **THEN** developers SHALL extend the timeline model and corresponding row renderer
- **AND** they SHALL not be required to modify unrelated row grouping and visibility logic across the full conversation component

#### Scenario: Typed rows form a closed discriminated union
- **WHEN** the timeline builder emits row models
- **THEN** those rows SHALL use a closed discriminated union rather than a generic message bag with ad hoc predicates
- **AND** the model SHALL distinguish source rows from synthetic or aggregate rows explicitly

### Requirement: Live overlay ownership SHALL be explicit relative to the timeline
The architecture SHALL define whether live overlay state is a timeline projection, a separate surface, or a coordinated combination, and it SHALL avoid double-rendering the same runtime state.

#### Scenario: Overlay and timeline rows do not duplicate the same runtime event
- **WHEN** live overlay state and live stage/timeline rows describe the same underlying runtime activity
- **THEN** the system SHALL define which surface owns the visible representation
- **AND** duplicate rendering or duplicate hiding behavior SHALL not be left to implicit component branching

### Requirement: Streaming updates SHALL preserve historical row stability
The architecture SHALL preserve stable row identity and viewport behavior for unchanged history while live content updates.

#### Scenario: Existing rows remain stable while live content changes
- **WHEN** new deltas arrive for the active turn
- **THEN** unchanged historical rows SHALL retain stable identifiers and reused derived view data
- **AND** the UI SHALL avoid reinterpreting the entire message list as a fresh render pass

#### Scenario: Bottom-follow and detached reading remain explicit states
- **WHEN** the user is either pinned to the latest output or reading older content
- **THEN** the conversation model SHALL preserve those two reading modes explicitly
- **AND** streaming updates SHALL not collapse them into one implicit scroll behavior

#### Scenario: Scroll behavior follows an explicit state machine
- **WHEN** the user switches threads, restores saved position, receives streaming updates, or encounters image/overlay-only layout changes
- **THEN** the conversation system SHALL treat `follow-latest`, `detached`, and `restore-thread-position` as explicit modes
- **AND** updates SHALL not snap the viewport unexpectedly or erase saved thread position
