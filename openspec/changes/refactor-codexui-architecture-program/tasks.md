## 1. Foundations, shell, and routing

- [ ] 1.1 Record the current architecture hotspots, bundle baseline artifacts, and manual regression baseline for `App.vue`, `useDesktopState.ts`, `ThreadConversation.vue`, `ThreadComposer.vue`, `httpServer.ts`, and `vite.config.ts`
- [ ] 1.2 Add canonical verification commands for unit, component, and smoke coverage that can run locally and in CI
- [ ] 1.3 Create initial tests for timeline ordering/reconciliation and at least one composer or conversation contract before major refactor slices land
- [ ] 1.4 Define a phase smoke matrix and post-build module-load smoke path for later routing/runtime slices

- [ ] 2.1 Introduce concrete route page components for home, thread, and skills screens
- [ ] 2.2 Reduce `App.vue` to shell/layout responsibilities and move page-specific watchers and composition into route-owned pages
- [ ] 2.3 Replace bidirectional route/thread synchronization with a single route-owned screen selection flow
- [ ] 2.4 Preserve the existing route contract, including `createWebHashHistory()`, `home/thread/skills` route names, `/new-thread` redirect, and catch-all fallback
- [ ] 2.5 Validate direct thread navigation, invalid-thread fallback, `openProjectPath` bootstrap, and route-level lazy loading behavior

## 2. Desktop state domains and conversation timeline

- [ ] 3.1 Split internal desktop state into domain modules for thread index, thread runtime, live timeline, runtime preferences, workspace flows, bridge/session-control, and session-capabilities
- [ ] 3.2 Keep a stable `useDesktopState()` façade while preventing new cross-domain façade growth during migration
- [ ] 3.3 Define notification ownership and normalization seams before domain state updates
- [ ] 3.4 Break `codexGateway.ts` into scoped gateway modules that match the new domain boundaries, including bridge notifications, server requests, accounts/quota, composer/local-file, and integrations
- [ ] 3.5 Migrate page and component consumers to the smallest relevant domain-facing selectors/actions and eliminate unnecessary broad gateway imports

- [ ] 4.1 Extract a canonical timeline builder that merges persisted thread snapshots and live runtime events into typed row models with stable `rowId`, `rowKind`, `orderKey`, and `sourceMessageIds`
- [ ] 4.2 Define reconciliation rules for segmented live output, silent refresh replacement, duplicate live/persisted rows, and late turn metadata rebinding
- [ ] 4.3 Split `ThreadConversation.vue` into row-oriented rendering components or equivalent row-owned render branches driven by a closed discriminated union of typed view models
- [ ] 4.4 Preserve stable history rendering, explicit scroll/follow modes, and live overlay ownership while migrating conversation rendering
- [ ] 4.5 Add regression coverage for tool/text interleaving, live overlay state, unchanged-history stability, and scroll-mode transitions during streaming

## 3. Bridge host unification, rollout, and documentation

- [ ] 5.1 Extract shared bridge registration and local-file route registration so development and production hosts reuse the same implementation
- [ ] 5.2 Update Vite and production server entrypoints to compose shared host modules instead of duplicating inline route logic
- [ ] 5.3 Make the canonical host inventory explicit for `/codex-api/rpc`, `/codex-api/meta/*`, `/codex-api/server-requests/*`, `/codex-api/events`, `/codex-api/ws`, `/codex-local-image`, `/codex-local-file`, `/codex-local-directories`, `/codex-local-open/*path`, `/codex-local-browse/*path`, and `/codex-local-edit/*path`
- [ ] 5.4 Verify WebSocket readiness, SSE fallback, auth-wrapped upgrade semantics, and local-file HTTP semantics behave the same in development and production modes

- [ ] 6.1 Remove transitional adapters, dead code, and duplicated helper paths that are no longer needed after migration
- [ ] 6.2 Update `tests.md` with the final manual regression path and phase smoke matrix for the new architecture slices
- [ ] 6.3 Rebuild bundle/performance baseline artifacts and compare them phase by phase
- [ ] 6.4 Confirm each migration phase remains independently releasable with explicit entry/exit criteria, rollback points, and verification evidence
