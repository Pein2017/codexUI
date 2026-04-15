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
