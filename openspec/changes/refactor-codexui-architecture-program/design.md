## Context

`codexUI` currently behaves like a compact browser IDE for Codex, but its implementation concentrates most orchestration in a few oversized files:

- `src/App.vue` owns shell layout, route interpretation, home/new-thread flows, thread screen composition, settings, and several cross-screen watchers.
- `src/composables/useDesktopState.ts` owns persisted thread state, live notification ingestion, queueing, runtime preferences, workspace state, and reconciliation logic behind one broad API.
- `src/components/content/ThreadConversation.vue` owns message classification, grouping, hiding, live overlay state, markdown parsing, diff viewing, and scroll management.
- `src/server/httpServer.ts` and `vite.config.ts` both register similar bridge and local-file routes, which creates avoidable drift risk.

Recent UI work showed the architectural cost of this concentration. Improvements to streaming behavior, timeline ordering, and live overlay presentation required touching state ingestion, list derivation, and rendering in parallel. That pattern is manageable for isolated fixes, but it scales poorly for larger features such as route-level screen growth, new runtime event types, test automation, or server-host capabilities.

Constraints:

- Preserve existing user-visible behavior unless a refactor slice intentionally improves it.
- Continue to support the Codex app-server bridge contract and current local-file workflows.
- Avoid a flag day rewrite; the system must remain shippable after each migration phase.
- Keep the implementation friendly to later agents by leaving explicit seams, stable ownership, and replayable verification steps.

Stakeholders:

- Localhost users who care about responsiveness and stable live rendering.
- Maintainers who need to land UI changes without repeatedly editing the same giant files.
- Future feature work for review, skills, workspace browsing, and richer runtime events.

## Goals / Non-Goals

**Goals:**

- Introduce route-owned page boundaries and reduce the root shell to persistent layout concerns.
- Split desktop state into domain-owned modules while preserving a migration façade.
- Define one canonical conversation timeline model that merges persisted and live runtime data deterministically.
- Separate conversation row modeling from row rendering to reduce component complexity and improve rendering stability.
- Unify dev/prod bridge registration so server-backed capabilities have one canonical implementation.
- Establish a verification ladder for architecture work: pure logic tests, key UI contract coverage, and maintained manual regression steps.

**Non-Goals:**

- Rewriting the app in a different frontend framework.
- Replacing the Codex app-server protocol or redesigning server RPC semantics.
- Replacing all existing component styling or redesigning the visual system as part of this change.
- Introducing full application-wide virtualization, SSR, or a new deployment model in the first migration slice.

## Decisions

### Decision: Make route components the owners of screen-specific behavior

`App.vue` will become a shell that renders persistent layout, top-level providers, and the sidebar frame. Real route components will own:

- home/new-thread behavior
- thread page behavior
- skills page behavior
- optional nested thread sub-surfaces such as review

Rationale:

- This removes the need for the current route/state synchronization watchers.
- It creates natural lazy-loading boundaries.
- It localizes screen lifecycles and side effects.

Alternatives considered:

- Keep `App.vue` as the main controller and only extract smaller child components.
  Rejected because it reduces template size but does not fix ownership ambiguity.
- Switch immediately to a file-based router or new app framework.
  Rejected because the migration cost is higher than needed for the current codebase.

### Decision: Retain a façade over desktop state during migration

Instead of replacing `useDesktopState()` in one step, the implementation will move internal logic into domain modules and keep a façade that current consumers can still use until migration is complete.

Target domain boundaries:

- thread index state
- thread runtime state
- live timeline state
- composer/runtime preference state
- workspace/new-thread state

Rationale:

- Existing consumers can migrate gradually.
- Internal ownership becomes explicit without forcing a wide branch of breaking edits.
- The façade gives one rollback point if a slice regresses.

Alternatives considered:

- Immediate migration to Pinia across the whole app.
  Rejected for the first phase because the library change would obscure whether improvements came from better boundaries or just from a new container.
- Keep the single composable and only add comments/regions.
  Rejected because it does not materially reduce coupling.

### Decision: Introduce a canonical timeline builder between state and conversation rendering

The thread view will be derived through a pure timeline builder:

- input: authoritative thread snapshot + live runtime state
- output: typed row view models in display order

Conversation rendering will then consume those row models through smaller row-focused components.

Rationale:

- The same model can support chronological tool/text interleaving, hidden-row grouping, and future runtime event types.
- Pure modeling logic is easier to test than implicit template branching.
- Rendering performance improves when unchanged history can keep stable row models.

Alternatives considered:

- Continue evolving `ThreadConversation.vue` with more caches and local computed sets.
  Rejected because the core complexity problem is ownership and derivation sprawl, not merely cache coverage.
- Push all rendering decisions into `useDesktopState()`.
  Rejected because state ownership and view-model ownership are related but distinct concerns.

### Decision: Split gateway and bridge host code by capability

The current broad gateway surface and duplicated host registration code will be split into capability-oriented modules.

Frontend target seams:

- `api/gateway/threads`
- `api/gateway/session`
- `api/gateway/review`
- `api/gateway/workspace`
- `api/gateway/skills`

Server target seams:

- shared bridge host registration
- local-file route registration
- auth registration
- feature-specific server route registration

Rationale:

- Domain state can depend on narrower APIs.
- Dev and prod hosts can share one registration contract.
- Future features stop inflating one file.

Alternatives considered:

- Keep a single gateway file and only reorder exports.
  Rejected because dependency breadth would remain unchanged.
- Keep separate dev/prod implementations with stricter copy discipline.
  Rejected because duplicate implementations naturally drift over time.

### Decision: Build verification around extracted pure logic and a small regression ladder

The refactor will not rely on manual checking alone. Each slice will add or preserve:

- unit tests for extracted pure logic
- component tests or smoke browser tests for critical UI contracts
- updated `tests.md` entries for manual verification

Rationale:

- Architecture work changes multiple files at once and needs regression evidence.
- Pure logic extraction is only valuable if it becomes independently testable.
- Small smoke tests are sufficient for confidence without blocking every slice on a large browser suite.

Alternatives considered:

- Stay manual-first and document all checks in `tests.md`.
  Rejected because broad architecture changes need faster, repeatable confidence.
- Add a large end-to-end suite before any refactor.
  Rejected because it delays the actual architecture work and is unnecessary for the first slices.

## Risks / Trade-offs

- [Migration fatigue from too many seams at once] → Mitigation: land route, state, timeline, and bridge refactors in staged slices with façade compatibility.
- [Temporary duplication during the migration window] → Mitigation: allow narrow short-lived adapters, but require each phase to remove or isolate its transitional layer before the next large slice.
- [Behavior drift between live timeline logic and persisted snapshot logic] → Mitigation: centralize reconciliation in a pure timeline builder with explicit tests for ordering and deduplication.
- [Route extraction can move bugs rather than remove them] → Mitigation: start with shell/page ownership only, keep behavior stable, and use smoke tests for thread open, send, and navigation.
- [Verification overhead can slow feature delivery] → Mitigation: keep the automated layer intentionally small and focused on extracted pure logic plus core user flows.
- [Bundle splitting can increase navigation-time loading cost] → Mitigation: use route-level lazy loading only for true page boundaries and measure build output after each phase.

## Migration Plan

### Phase 1: Foundations and guardrails

- Add local OpenSpec artifacts for the refactor program.
- Introduce automated test support for extracted pure logic and small UI contracts.
- Record current build output and a manual smoke baseline.

### Phase 2: Shell and routing ownership

- Create dedicated route components for home, thread, and skills screens.
- Reduce `App.vue` to shell responsibilities.
- Remove bidirectional route/thread synchronization loops in favor of route-owned screen logic.

### Phase 3: State-domain extraction

- Introduce internal domain state modules behind the existing desktop-state façade.
- Split gateway surfaces to match domain ownership.
- Migrate one consumer group at a time to the new domain seams.

### Phase 4: Conversation timeline refactor

- Extract timeline building and row modeling from `ThreadConversation.vue`.
- Introduce row-oriented renderers for assistant text, tools, file changes, and live stages.
- Preserve current behavior while shrinking the conversation component's direct responsibilities.

### Phase 5: Bridge host unification and rollout hardening

- Move shared dev/prod bridge registration into canonical route/host modules.
- Remove duplicated bridge endpoint implementations from host entrypoints.
- Re-run build, smoke checks, and architecture-focused regressions.

Rollback strategy:

- Each phase must remain independently shippable.
- The façade around desktop state and the shell-level route boundary provide rollback points if a later phase regresses.
- No phase should depend on an unfinished later phase to keep the app functional.

## Open Questions

- Should Pinia become the long-term public state surface after the domain split stabilizes, or is a composable façade sufficient?
- Which parts of conversation history, if any, should later adopt virtualization once row modeling is in place?
- Should the repository fully adopt feature-first directory ownership, or only for the modules touched by this refactor program?
