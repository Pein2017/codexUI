## ADDED Requirements

### Requirement: Extracted architecture logic SHALL be covered by automated tests
Pure logic introduced by the refactor SHALL be extracted into testable modules and covered by automated verification.

#### Scenario: Timeline and normalization logic is unit tested
- **WHEN** timeline-building, row-modeling, or normalization logic is extracted from state or view components
- **THEN** that logic SHALL have automated tests that verify ordering, reconciliation, and type-specific output

#### Scenario: State-domain selectors and reducers are exercised outside the browser
- **WHEN** domain modules expose selectors or pure state transitions
- **THEN** those seams SHALL be verified without requiring end-to-end browser execution

### Requirement: Critical UI contracts SHALL have targeted component or browser-level coverage
The refactor SHALL preserve important user flows through a small but explicit regression surface.

#### Scenario: Conversation and composer contracts are exercised
- **WHEN** conversation or composer architecture changes land
- **THEN** the project SHALL verify at least the critical flows for sending, switching threads, and rendering live runtime output through component tests, smoke browser tests, or both

#### Scenario: Manual verification remains documented for architecture slices
- **WHEN** a refactor slice changes user-visible behavior or runtime interaction
- **THEN** `tests.md` SHALL document the manual verification path for that slice alongside any automated coverage

### Requirement: Architecture refactor slices SHALL be independently releasable
Each migration slice SHALL be small enough to verify and ship without requiring all later phases to be complete.

#### Scenario: Intermediate façade-backed migrations remain valid
- **WHEN** only some pages or state domains have migrated to the new architecture
- **THEN** the application SHALL remain functional and verifiable without waiting for the final architecture state

#### Scenario: Performance and bundle baselines can be compared phase by phase
- **WHEN** a migration slice changes routing, rendering, or build boundaries
- **THEN** the project SHALL be able to compare build output or targeted runtime behavior before and after that slice
