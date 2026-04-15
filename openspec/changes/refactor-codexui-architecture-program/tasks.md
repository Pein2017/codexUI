## 1. Baseline and verification scaffolding

- [ ] 1.1 Record the current architecture hotspots, bundle baseline, and manual regression baseline for `App.vue`, `useDesktopState.ts`, `ThreadConversation.vue`, `ThreadComposer.vue`, `httpServer.ts`, and `vite.config.ts`
- [ ] 1.2 Add automated test tooling for extracted pure logic and lightweight component contracts
- [ ] 1.3 Create initial tests for timeline ordering/reconciliation and at least one composer or conversation contract before major refactor slices land

## 2. Route shell and page ownership

- [ ] 2.1 Introduce concrete route page components for home, thread, and skills screens
- [ ] 2.2 Reduce `App.vue` to shell/layout responsibilities and move page-specific watchers and composition into route-owned pages
- [ ] 2.3 Replace bidirectional route/thread synchronization with a single route-owned screen selection flow
- [ ] 2.4 Validate that route-level lazy loading preserves current navigation behavior and reduces eager page loading

## 3. Desktop state domain extraction

- [ ] 3.1 Split internal desktop state into domain modules for thread index, thread runtime, live timeline, runtime preferences, and workspace flows
- [ ] 3.2 Keep a stable `useDesktopState()` façade while migrating current consumers to the new internal domain seams
- [ ] 3.3 Break `codexGateway.ts` into scoped gateway modules that match the new domain boundaries
- [ ] 3.4 Migrate page and component consumers to the smallest relevant domain-facing selectors and actions

## 4. Conversation timeline and renderer refactor

- [ ] 4.1 Extract a canonical timeline builder that merges persisted thread snapshots and live runtime events into typed row models
- [ ] 4.2 Split `ThreadConversation.vue` into row-oriented rendering components or equivalent row-owned render branches driven by typed view models
- [ ] 4.3 Preserve stable history rendering, scroll behavior, and live interleaving semantics while migrating conversation rendering
- [ ] 4.4 Add regression coverage for tool/text interleaving, live overlay state, and unchanged-history stability during streaming

## 5. Bridge host unification

- [ ] 5.1 Extract shared bridge registration and local-file route registration so development and production hosts reuse the same implementation
- [ ] 5.2 Update Vite and production server entrypoints to compose shared host modules instead of duplicating inline route logic
- [ ] 5.3 Verify WebSocket readiness, notification payload shape, and local-file routes behave the same in both development and production modes

## 6. Cleanup, rollout, and documentation

- [ ] 6.1 Remove transitional adapters, dead code, and duplicated helper paths that are no longer needed after migration
- [ ] 6.2 Update `tests.md` with the final manual regression path for the new architecture slices
- [ ] 6.3 Rebuild bundle baselines and confirm the refactor remains behaviorally stable and independently shippable phase by phase
