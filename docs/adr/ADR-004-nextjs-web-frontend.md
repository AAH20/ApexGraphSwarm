# ADR-004: Next.js web frontend with separate npm dependencies

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system needs a rich interactive UI for graph exploration, team design, swarm control, delegation planning, analytics, and evaluation. The frontend must support WebGL rendering, force layouts, real-time updates, and complex state management. It must be separate from the Python control plane to allow independent development and deployment.

## Decision

**Next.js (React/TypeScript)** is the web frontend framework, located in `apps/web/`. Key characteristics:

- **Separate npm dependencies**: The web app has its own `package.json` and `package-lock.json`; it does not share dependencies with the Python control plane.
- **API routes**: Next.js API routes provide the bridge between the frontend and the Python control plane (via subprocess or direct function calls).
- **WebGL rendering**: The graph visualization uses WebGL with an SVG fallback for accessibility.
- **Port 3010**: Development and production both use port 3010 by default.
- **Type safety**: TypeScript with strict type checking; `npm run typecheck` and `npm run build` are required for frontend changes.

## Alternatives considered

1. **Plain HTML/JS with no framework**: Would eliminate npm dependencies but would require manual DOM management, state handling, and build tooling for the complex UI.
2. **Vue/Svelte**: Would be viable alternatives but React/TypeScript has a larger ecosystem for graph visualization, force layouts, and complex state management.
3. **Python-based web framework (Flask/FastAPI + Jinja)**: Would unify the language stack but would require a separate process for the web server, complicate the local-first deployment, and limit the rich interactivity needed for graph exploration.
4. **Electron desktop app**: Would provide native desktop integration but adds significant complexity, binary size, and platform-specific builds without clear benefit for a local-first web app.

## Consequences

- **Positive**: Rich interactive UI; strong TypeScript ecosystem; mature graph visualization libraries; independent deployment; large developer community.
- **Negative**: Separate dependency tree from Python; requires Node.js/npm; build step needed; larger repository size due to `node_modules`.
- **Integration**: The frontend communicates with the Python control plane through well-defined API contracts; the control plane never imports frontend code.

## Related

- ADR-001 (local-first architecture)
- ADR-002 (stdlib-only control plane)
- ADR-012 (explicit adapter pattern)
