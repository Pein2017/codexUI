## Why

`codexUI` has grown from a lightweight browser shell into a mixed system that now owns page orchestration, live conversation rendering, runtime controls, local file browsing, and the Codex app-server bridge. The current implementation still works, but the heaviest responsibilities are concentrated in a few very large files, which makes the next wave of UI work slower, riskier, and harder to verify.

This change is needed now because recent work on localhost responsiveness, live timeline ordering, and runtime overlay behavior has shown that even medium-sized UX improvements require touching shared state, rendering rules, and bridge behavior at the same time. Without a clearer architecture, future features will continue to compound complexity inside the same hot spots.

## What Changes

- Introduce a route-owned app shell so `App.vue` stops acting as the controller for every screen and interaction flow.
- Preserve the current route contract, startup bootstrap behavior, and thread deep-link fallback while moving screen ownership to real route pages.
- Split the monolithic desktop state composable into explicit domain modules while preserving a stable façade for incremental migration.
- Formalize a canonical conversation timeline pipeline that merges persisted thread snapshots with live runtime events in one deterministic stream.
- Define a row-level contract for conversation ordering, identity, reconciliation, scroll state, and live overlay ownership so the timeline refactor is behaviorally well-specified.
- Separate conversation row modeling from conversation row rendering so assistant text, tool events, live stages, and overlays can evolve without further inflating one component.
- Unify development and production bridge/server route registration so local-file, transport fallback, auth-wrapped WebSocket behavior, and Codex bridge behavior do not diverge across environments.
- Add an explicit verification surface for architecture work, including canonical automated commands, bundle/performance artifacts, phase smoke matrices, and post-build runtime/module-load checks.

## Capabilities

### New Capabilities
- `app-shell-routing`: Define route-owned page boundaries and reduce `App.vue` to layout and shell responsibilities.
- `desktop-state-domains`: Organize desktop state into domain-oriented modules with explicit ownership for thread index, runtime session state, live timeline state, and workspace state.
- `conversation-timeline`: Build the thread view from a deterministic timeline model that interleaves persisted messages and live runtime events in chronological order.
- `bridge-runtime-host`: Share one canonical bridge/runtime host registration model across Vite development and the production Express server.
- `quality-verification`: Establish architecture-focused automated verification for extracted pure logic, key UI contracts, and a small manual smoke checklist.

### Modified Capabilities
- None.

## Impact

- Frontend shell and route composition in `src/App.vue` and `src/router/index.ts`
- State management and event ingestion in `src/composables/useDesktopState.ts`
- Conversation rendering and live runtime presentation in `src/components/content/ThreadConversation.vue`
- Composer ownership and runtime controls in `src/components/content/ThreadComposer.vue`
- RPC/service boundaries in `src/api/codexGateway.ts` and `src/api/codexRpcClient.ts`
- Dev/prod bridge hosting in `src/server/httpServer.ts` and `vite.config.ts`
- Build/test workflow in `package.json` and `tests.md`
