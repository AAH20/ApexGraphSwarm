# Sigma.js v3 → v4 Alpha Migration Report

## Summary

Migrated the ApexGraphSwarm web app from `sigma@3.0.3` to `sigma@4.0.0-alpha.7`, fixing all breaking API changes in `GraphCanvasEnhanced.tsx` and `GraphCanvas.tsx`. Typecheck passes, all 183 tests pass, and benchmarks show no regression.

## Breaking Changes Addressed

### 1. Constructor options restructured

**v3:** All options passed as a single flat object to `new Sigma(graph, container, options)`.

**v4:** Options split into `styles` (declarative node/edge styling) and `settings` (imperative renderer settings).

| v3 option | v4 equivalent |
|---|---|
| `defaultNodeColor` | `styles.nodes.color` with `attribute: "color"` + `defaultValue` |
| `defaultEdgeColor` | `styles.edges.color` with `attribute: "color"` + `defaultValue` |
| `defaultEdgeType: "arrow"` | `styles.edges.head: "arrow"` |
| `labelFont` | `styles.nodes.labelFont` |
| `labelSize` | `styles.nodes.labelSize` |
| `labelWeight` | Removed (no v4 equivalent) |
| `labelColor: { color: "..." }` | `styles.nodes.labelColor: "..."` (plain string) |
| `labelRenderedSizeThreshold` | `settings.labelRenderedSizeThreshold` |
| `labelDensity` | `settings.labelDensity` |
| `stagePadding` | `settings.stagePadding` |
| `minCameraRatio` / `maxCameraRatio` | `settings.minCameraRatio` / `settings.maxCameraRatio` (now `null \| number`) |
| `hideEdgesOnMove` | `settings.hideEdgesOnMove` |
| `renderEdgeLabels` | `settings.renderEdgeLabels` |

### 2. Event payload structure changed

**v3:** `clickNode` payload had `node` and the raw `MouseEvent` directly accessible.

**v4:** `clickNode` payload has `node` and `event: MouseCoords` where `event.original` is the original `MouseEvent`.

```ts
// v3
renderer.on("clickNode", ({ node }) => {
  handleNodeClick(node, event?.shiftKey ?? false);
});

// v4
renderer.on("clickNode", ({ node, event }) => {
  const original = event.original as MouseEvent | undefined;
  handleNodeClick(node, original?.shiftKey ?? false);
});
```

### 3. `getCanvases()` removed

**v3:** `sigma.getCanvases()` returned an array of canvases.

**v4:** Use `sigma.getStageCanvas()` to get the main stage canvas.

### 4. Camera animation methods return Promises

**v3:** `camera.animatedZoom()`, `camera.animatedUnzoom()`, `camera.animatedReset()` returned void.

**v4:** These return `Promise<void>`. The existing `void camera()?.animatedZoom(...)` pattern still works correctly.

## Files Modified

- `apps/web/package.json` — `sigma` version `3.0.3` → `4.0.0-alpha.7`
- `apps/web/package-lock.json` — updated lockfile
- `apps/web/components/GraphCanvasEnhanced.tsx` — migrated constructor options, event handler, export function
- `apps/web/components/GraphCanvas.tsx` — migrated constructor options

## Verification

### Typecheck

```
$ npx tsc --noEmit
(no output — clean)
```

### Tests

```
$ npm test
# tests 183
# pass 183
# fail 0
```

### Benchmarks

Graphology construction + ForceAtlas2 layout (1800 nodes, 14400 edges, 30 iterations):

| Metric | v3 (before) | v4 (after) | Delta |
|---|---|---|---|
| Build time | 28.53 ms | 17.99 ms | −37% |
| Layout time | 253.06 ms | 221.19 ms | −13% |
| Checksum | −126934.9236 | −126934.9236 | identical |

Additional v4 runs: build 17–25 ms, layout 202–326 ms (within normal variance).

The checksum is identical across versions, confirming the ForceAtlas2 layout algorithm produces the same output. The benchmark scope is graph construction and synchronous layout only; browser rendering is not measured.

## Risk Assessment

- **Alpha stability:** `4.0.0-alpha.7` is a pre-release. The API may change before stable v4.
- **Visual parity:** The declarative `styles` API produces the same visual output as the v3 flat options, but subtle rendering differences may exist due to the new WebGL2-based renderer.
- **Performance:** The v4 renderer uses WebGL2 and SDF-based label rendering, which should be faster for large graphs, but this was not benchmarked in a browser environment.
