## ADDED Requirements

### Requirement: Extracted architecture logic SHALL be covered by automated tests
Pure logic introduced by the refactor SHALL be extracted into testable modules and covered by automated verification.

#### Scenario: Timeline and normalization logic is unit tested
- **WHEN** timeline-building, row-modeling, or normalization logic is extracted from state or view components
- **THEN** that logic SHALL have automated tests that verify ordering, reconciliation, and type-specific output

#### Scenario: State-domain selectors and reducers are exercised outside the browser
- **WHEN** domain modules expose selectors or pure state transitions
- **THEN** those seams SHALL be verified without requiring end-to-end browser execution

### Requirement: Verification SHALL be invokable through canonical commands
The project SHALL expose a small canonical verification command surface so architecture slices can be run locally and in automation with the same entrypoints.

#### Scenario: Unit, component, and smoke commands are explicit
- **WHEN** the architecture program adds automated verification
- **THEN** the repository SHALL expose canonical commands for unit, component, and smoke verification
- **AND** those commands SHALL be usable from both local workflows and CI

### Requirement: Critical UI contracts SHALL have targeted component or browser-level coverage
The refactor SHALL preserve important user flows through a small but explicit regression surface.

#### Scenario: Conversation and composer contracts are exercised
- **WHEN** conversation or composer architecture changes land
- **THEN** the project SHALL verify at least the critical flows for sending, switching threads, and rendering live runtime output through component tests, smoke browser tests, or both

#### Scenario: Manual verification remains documented for architecture slices
- **WHEN** a refactor slice changes user-visible behavior or runtime interaction
- **THEN** `tests.md` SHALL document the manual verification path for that slice alongside any automated coverage

#### Scenario: Each migration phase has a minimum smoke matrix
- **WHEN** a migration phase lands
- **THEN** that phase SHALL define the smallest required smoke subset for its changed surface
- **AND** the smoke matrix SHALL cover route/navigation flows, timeline/live-output flows, or bridge/runtime parity as appropriate for that phase

### Requirement: Build and performance baselines SHALL be recorded as artifacts
The refactor SHALL leave behind comparable build and runtime baseline artifacts for slices that change routing, rendering, or host boundaries.

#### Scenario: Bundle artifacts are comparable before and after route changes
- **WHEN** routing or lazy-loading boundaries change
- **THEN** the project SHALL record comparable bundle artifacts including initial JS/CSS size and route-related chunk membership
- **AND** those artifacts SHALL be sufficient to verify that deferred screens such as `skills` or review-specific code remain outside the initial route load when intended

#### Scenario: Runtime behavior baselines are captured for timeline changes
- **WHEN** conversation rendering or scrolling behavior changes
- **THEN** the project SHALL capture at least a small targeted runtime baseline for thread-open responsiveness or streaming stability
- **AND** that baseline SHALL be comparable before and after the migration slice

### Requirement: Architecture refactor slices SHALL be independently releasable
Each migration slice SHALL be small enough to verify and ship without requiring all later phases to be complete.

#### Scenario: Intermediate façade-backed migrations remain valid
- **WHEN** only some pages or state domains have migrated to the new architecture
- **THEN** the application SHALL remain functional and verifiable without waiting for the final architecture state

#### Scenario: Performance and bundle baselines can be compared phase by phase
- **WHEN** a migration slice changes routing, rendering, or build boundaries
- **THEN** the project SHALL be able to compare build output or targeted runtime behavior before and after that slice

#### Scenario: Build-boundary changes include post-build runtime smoke
- **WHEN** a migration slice changes runtime entrypoints, packaging boundaries, or host/module loading behavior
- **THEN** the slice SHALL include a post-build module-load or runtime smoke check
- **AND** that check SHALL run in addition to browser-only manual verification
