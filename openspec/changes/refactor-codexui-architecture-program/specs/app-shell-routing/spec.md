## ADDED Requirements

### Requirement: Route-owned screens SHALL define page responsibility boundaries
The application SHALL treat routing as the owner of screen-level behavior. The root shell SHALL provide persistent layout, shared sidebar chrome, and top-level providers, while route components SHALL own page-specific loading, watchers, and screen composition.

#### Scenario: Thread screen is resolved through a route component
- **WHEN** the user opens `/thread/:threadId`
- **THEN** the router SHALL resolve a dedicated thread page component instead of rendering an empty route placeholder
- **AND** that page component SHALL own thread-specific composition for conversation, composer, and review surfaces

#### Scenario: Non-thread screens do not inherit thread-only orchestration
- **WHEN** the user opens the home or skills screen
- **THEN** thread-only side effects such as review pane synchronization and thread message loading SHALL not run from the root shell

### Requirement: Router state SHALL be the single screen-selection authority
The application SHALL avoid duplicated ownership between route state and view state for determining the active screen and active thread context.

#### Scenario: Active thread follows navigation without bidirectional sync loops
- **WHEN** navigation changes from one thread route to another
- **THEN** the thread page SHALL derive the active thread context from the route
- **AND** the application SHALL not require paired watchers that continuously push route state back into local selection state and vice versa

#### Scenario: Leaving a thread route clears thread-only screen state
- **WHEN** the user navigates away from a thread route
- **THEN** thread-page-only UI state SHALL be released by the thread page lifecycle rather than retained implicitly by the root shell

### Requirement: Route-level code loading SHALL create real screen boundaries
The application SHALL lazy-load page-sized features at route boundaries so the initial shell does not eagerly load all screen implementations.

#### Scenario: Skills screen is deferred until requested
- **WHEN** the application first boots into the home or thread screen
- **THEN** the skills screen implementation SHALL remain outside the initial route bundle until the user navigates to the skills route

#### Scenario: Review screen logic is loaded from the thread route boundary
- **WHEN** a thread is opened without the review surface
- **THEN** review-specific screen code SHALL not be required to establish the base thread experience
