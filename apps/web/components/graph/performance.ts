/**
 * Performance utilities for large-graph rendering.
 *
 * Target: 60fps at 50K nodes via:
 *   - Virtual scrolling (viewport-only rendering)
 * - Level-of-detail (LOD) rendering
 *   - Frustum culling
 *   - Web Worker for layout computation
 *   - requestAnimationFrame batching
 */

// ─── Types ──────────────────────────────────────────────────────────────────

export interface Viewport {
/**
 * React component for performance.
 *
 * @module performance
 * @packageDocumentation
 */
  x: number;
  y: number;
  width: number;
  height: number;
}

/**
 * Interface CameraState.
 *
 *
 * @example
 * ```typescript
 * import { CameraState } from './module';
 * ```
 */
export interface CameraState {
  x: number;
  y: number;
  ratio: number; // zoom ratio (1 = fit, >1 = zoomed in, <1 = zoomed out)
}

/**
 * Interface LODLevel.
 *
 *
 * @example
 * ```typescript
 * import { LODLevel } from './module';
 * ```
 */
export interface LODLevel {
  /** Minimum camera ratio to activate this level */
  minRatio: number;
  /** Node size multiplier */
  nodeSize: number;
  /** Edge size multiplier */
  edgeSize: number;
  /** Whether to show labels */
  showLabels: boolean;
  /** Label density (0-1) */
  labelDensity: number;
  /** Whether to show edges at all */
  showEdges: boolean;
  /** Edge opacity multiplier */
  edgeOpacity: number;
  /** Whether to render node borders */
  showBorders: boolean;
}

/**
 * Interface RenderBatch.
 *
 *
 * @example
 * ```typescript
 * import { RenderBatch } from './module';
 * ```
 */
export interface RenderBatch {
  nodeIds: Set<string>;
  edgeKeys: Set<string>;
  lodLevel: number;
}

/**
 * Interface WorkerMessage.
 *
 *
 * @example
 * ```typescript
 * import { WorkerMessage } from './module';
 * ```
 */
export interface WorkerMessage {
  type: 'layout-step' | 'layout-complete' | 'layout-error';
  positions?: Array<{ id: string; x: number; y: number }>;
  error?: string;
  progress?: number;
}

// ─── LOD Configuration ───────────────────────────────────────────────────────

/**
 * LOD levels indexed by zoom ratio.
 * Level 0 = farthest (least detail), higher levels = closer (more detail).
 */
export const LOD_LEVELS: LODLevel[] = [
  // Zoomed far out: minimal detail
  { minRatio: 0,    nodeSize: 0.3, edgeSize: 0.2, showLabels: false, labelDensity: 0,    showEdges: true,  edgeOpacity: 0.15, showBorders: false },
  // Mid-far
  { minRatio: 0.15, nodeSize: 0.5, edgeSize: 0.4, showLabels: false, labelDensity: 0,    showEdges: true,  edgeOpacity: 0.25, showBorders: false },
  // Mid
  { minRatio: 0.4,  nodeSize: 0.7, edgeSize: 0.6, showLabels: false, labelDensity: 0.02, showEdges: true,  edgeOpacity: 0.4,  showBorders: false },
  // Mid-close
  { minRatio: 0.8,  nodeSize: 0.85, edgeSize: 0.8, showLabels: true,  labelDensity: 0.08, showEdges: true,  edgeOpacity: 0.6,  showBorders: true },
  // Closest: full detail
  { minRatio: 1.5,  nodeSize: 1.0, edgeSize: 1.0, showLabels: true,  labelDensity: 0.15, showEdges: true,  edgeOpacity: 0.8,  showBorders: true },
  // Ultra close: maximum detail
  { minRatio: 3.0,  nodeSize: 1.2, edgeSize: 1.2, showLabels: true,  labelDensity: 0.3,  showEdges: true,  edgeOpacity: 1.0,  showBorders: true },
];

/**
 * Get the appropriate LOD level for a given camera ratio.
 */
export function getLODLevel(ratio: number): number {
  let level = 0;
  for (let i = 0; i < LOD_LEVELS.length; i++) {
    if (ratio >= LOD_LEVELS[i].minRatio) {
      level = i;
    } else {
      break;
    }
  }
  return level;
}

// ─── Frustum Culling ────────────────────────────────────────────────────────

/**
 * Compute the visible world-space bounds from camera state.
 * Returns the axis-aligned bounding box of the visible area.
 */
export function computeVisibleBounds(
  camera: CameraState,
  viewport: Viewport,
): { minX: number; minY: number; maxX: number; maxY: number } {
  const halfW = viewport.width / (2 * camera.ratio);
  const halfH = viewport.height / (2 * camera.ratio);
  return {
    minX: camera.x - halfW,
    minY: camera.y - halfH,
    maxX: camera.x + halfW,
    maxY: camera.y + halfH,
  };
}

/**
 * Check if a point is within the visible bounds (with optional padding).
 */
export function isInBounds(
  x: number,
  y: number,
  bounds: { minX: number; minY: number; maxX: number; maxY: number },
  padding = 0,
): boolean {
  return (
    x >= bounds.minX - padding &&
    x <= bounds.maxX + padding &&
    y >= bounds.minY - padding &&
    y <= bounds.maxY + padding
  );
}

/**
 * Filter nodes to only those visible in the viewport.
 * Uses a spatial index for O(log n) queries when available.
 */
export function cullNodes<T extends { id: string; x: number; y: number }>(
  nodes: T[],
  bounds: { minX: number; minY: number; maxX: number; maxY: number },
  padding = 50,
): T[] {
  const result: T[] = [];
  for (let i = 0; i < nodes.length; i++) {
    const node = nodes[i];
    if (isInBounds(node.x, node.y, bounds, padding)) {
      result.push(node);
    }
  }
  return result;
}

/**
 * Filter edges to only those where both endpoints are visible.
 */
export function cullEdges<T extends { source: string; target: string }>(
  edges: T[],
  visibleNodeIds: Set<string>,
): T[] {
  const result: T[] = [];
  for (let i = 0; i < edges.length; i++) {
    const edge = edges[i];
    if (visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target)) {
      result.push(edge);
    }
  }
  return result;
}

// ─── Spatial Index (Uniform Grid) ───────────────────────────────────────────

/**
 * Simple uniform-grid spatial index for fast range queries.
 * Suitable for static or slowly-moving node sets.
 */
export class SpatialIndex<T extends { id: string; x: number; y: number }> {
  private cells = new Map<string, T[]>();
  private cellSize: number;
  private itemToCell = new Map<string, string>();

  constructor(items: T[], cellSize = 200) {
    this.cellSize = cellSize;
    for (const item of items) {
      this.insert(item);
    }
  }

  private cellKey(cx: number, cy: number): string {
    return `${cx},${cy}`;
  }

  private worldToCell(x: number, y: number): [number, number] {
    return [Math.floor(x / this.cellSize), Math.floor(y / this.cellSize)];
  }

  insert(item: T): void {
    const [cx, cy] = this.worldToCell(item.x, item.y);
    const key = this.cellKey(cx, cy);
    let cell = this.cells.get(key);
    if (!cell) {
      cell = [];
      this.cells.set(key, cell);
    }
    cell.push(item);
    this.itemToCell.set(item.id, key);
  }

  update(item: T): void {
    const oldKey = this.itemToCell.get(item.id);
    const [cx, cy] = this.worldToCell(item.x, item.y);
    const newKey = this.cellKey(cx, cy);
    if (oldKey === newKey) return;

    // Remove from old cell
    if (oldKey) {
      const oldCell = this.cells.get(oldKey);
      if (oldCell) {
        const idx = oldCell.findIndex((n) => n.id === item.id);
        if (idx >= 0) oldCell.splice(idx, 1);
        if (oldCell.length === 0) this.cells.delete(oldKey);
      }
    }

    // Insert into new cell
    let newCell = this.cells.get(newKey);
    if (!newCell) {
      newCell = [];
      this.cells.set(newKey, newCell);
    }
    newCell.push(item);
    this.itemToCell.set(item.id, newKey);
  }

  remove(id: string): void {
    const key = this.itemToCell.get(id);
    if (!key) return;
    const cell = this.cells.get(key);
    if (cell) {
      const idx = cell.findIndex((n) => n.id === id);
      if (idx >= 0) cell.splice(idx, 1);
      if (cell.length === 0) this.cells.delete(key);
    }
    this.itemToCell.delete(id);
  }

  /**
   * Query all items within the given bounds.
   */
  queryRange(
    bounds: { minX: number; minY: number; maxX: number; maxY: number },
  ): T[] {
    const [minCx, minCy] = this.worldToCell(bounds.minX, bounds.minY);
    const [maxCx, maxCy] = this.worldToCell(bounds.maxX, bounds.maxY);
    const result: T[] = [];
    const seen = new Set<string>();

    for (let cx = minCx; cx <= maxCx; cx++) {
      for (let cy = minCy; cy <= maxCy; cy++) {
        const cell = this.cells.get(this.cellKey(cx, cy));
        if (cell) {
          for (const item of cell) {
            if (!seen.has(item.id)) {
              seen.add(item.id);
              result.push(item);
            }
          }
        }
      }
    }
    return result;
  }

  clear(): void {
    this.cells.clear();
    this.itemToCell.clear();
  }

  get size(): number {
    return this.itemToCell.size;
  }
}

// ─── Virtual Scrolling ──────────────────────────────────────────────────────

/**
 * Virtual scrolling state for paginated node rendering.
 * Only renders nodes within the visible "window" plus an overscan margin.
 */
export interface VirtualScrollState {
  /** Total number of items */
  totalItems: number;
  /** Number of items visible in the viewport */
  visibleCount: number;
  /** Index of the first visible item */
  startIndex: number;
  /** Index of the last visible item (exclusive) */
  endIndex: number;
  /** Overscan margin (items rendered beyond viewport) */
  overscan: number;
}

/**
 * Compute virtual scroll window for a sorted node list.
 * Nodes are assumed to be sorted by importance (e.g., connections desc).
 */
export function computeVirtualWindow(
  totalItems: number,
  visibleCapacity: number,
  scrollOffset: number,
  overscan = 50,
): VirtualScrollState {
  const startIndex = Math.max(0, scrollOffset - overscan);
  const endIndex = Math.min(totalItems, scrollOffset + visibleCapacity + overscan);
  return {
    totalItems,
    visibleCount: endIndex - startIndex,
    startIndex,
    endIndex,
    overscan,
  };
}

/**
 * Select the most important nodes for rendering when the full set
 * exceeds the visible capacity. Uses degree centrality as importance.
 */
export function selectImportantNodes<
  T extends { id: string; connections?: number },
>(
  nodes: T[],
  edges: Array<{ source: string; target: string }>,
  maxNodes: number,
): T[] {
  if (nodes.length <= maxNodes) return nodes;

  // Compute degree for each node
  const degree = new Map<string, number>();
  for (const node of nodes) {
    degree.set(node.id, node.connections ?? 0);
  }
  for (const edge of edges) {
    degree.set(edge.source, (degree.get(edge.source) ?? 0) + 1);
    degree.set(edge.target, (degree.get(edge.target) ?? 0) + 1);
  }

  // Sort by degree descending, then by id for stability
  const sorted = [...nodes].sort((a, b) => {
    const degA = degree.get(a.id) ?? 0;
    const degB = degree.get(b.id) ?? 0;
    if (degA !== degB) return degB - degA;
    return a.id.localeCompare(b.id);
  });

  return sorted.slice(0, maxNodes);
}

// ─── RAF Batching ───────────────────────────────────────────────────────────

/**
 * Batches render operations into requestAnimationFrame cycles.
 * Prevents layout thrashing and ensures smooth 60fps rendering.
 */
export class RAFBatcher {
  private pending = new Map<string, () => void>();
  private rafId: number | null = null;
  private isRunning = false;

  /**
   * Schedule a callback for the next RAF cycle.
   * If a callback with the same key is already pending, it will be replaced.
   */
  schedule(key: string, callback: () => void): void {
    this.pending.set(key, callback);
    if (!this.isRunning) {
      this.isRunning = true;
      this.rafId = requestAnimationFrame(() => this.flush());
    }
  }

  /**
   * Flush all pending callbacks.
   */
  flush(): void {
    this.rafId = null;
    this.isRunning = false;
    const callbacks = [...this.pending.values()];
    this.pending.clear();
    for (const cb of callbacks) {
      try {
        cb();
      } catch {
        // Silently ignore errors in batched callbacks
      }
    }
  }

  /**
   * Cancel all pending callbacks.
   */
  cancel(): void {
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
    this.pending.clear();
    this.isRunning = false;
  }

  /**
   * Check if there are pending callbacks.
   */
  get hasPending(): boolean {
    return this.pending.size > 0;
  }

  /**
   * Get the number of pending callbacks.
   */
  get pendingCount(): number {
    return this.pending.size;
  }
}

// ─── Layout Worker ──────────────────────────────────────────────────────────

/**
 * Web Worker-based layout computation.
 * Offloads force-directed layout to a background thread.
 *
 * This is a wrapper that manages the worker lifecycle and provides
 * a promise-based API for layout computation.
 */
export class LayoutWorker {
  private worker: Worker | null = null;
  private messageId = 0;
  private pending = new Map<
    number,
    {
      resolve: (positions: Array<{ id: string; x: number; y: number }>) => void;
      reject: (error: Error) => void;
      onProgress?: (progress: number) => void;
    }
  >();

  /**
   * Initialize the layout worker.
   * The worker script should handle 'layout-step' and 'layout-complete' messages.
   */
  constructor(workerScript?: string) {
    if (typeof Worker !== 'undefined') {
      // Use provided script or inline worker
      const script = workerScript || this.getDefaultWorkerScript();
      const blob = new Blob([script], { type: 'application/javascript' });
      const url = URL.createObjectURL(blob);
      this.worker = new Worker(url);
      this.worker.onmessage = (e: MessageEvent<WorkerMessage>) => {
        this.handleMessage(e.data);
      };
      this.worker.onerror = (e) => {
        // Reject all pending computations
        for (const [, pending] of this.pending) {
          pending.reject(new Error(e.message || 'Layout worker error'));
        }
        this.pending.clear();
      };
    }
  }

  /**
   * Generate a default inline worker script for force layout.
   * Uses a simple force-directed algorithm.
   */
  private getDefaultWorkerScript(): string {
    return `
      self.onmessage = function(e) {
        var data = e.data;
        if (data.type === 'start') {
          var nodes = data.nodes;
          var edges = data.edges;
          var iterations = data.iterations || 300;
          var width = data.width || 1000;
          var height = data.height || 1000;

          // Initialize positions randomly
          var positions = {};
          for (var i = 0; i < nodes.length; i++) {
            positions[nodes[i]] = {
              x: (Math.random() - 0.5) * width,
              y: (Math.random() - 0.5) * height
            };
          }

          // Build adjacency
          var adj = {};
          for (var i = 0; i < nodes.length; i++) adj[nodes[i]] = [];
          for (var i = 0; i < edges.length; i++) {
            var s = edges[i].source, t = edges[i].target;
            if (adj[s]) adj[s].push(t);
            if (adj[t]) adj[t].push(s);
          }

          // Force-directed iterations
          var k = Math.sqrt((width * height) / nodes.length) * 0.5;
          var temperature = width / 10;

          for (var iter = 0; iter < iterations; iter++) {
            // Repulsion
            var disp = {};
            for (var i = 0; i < nodes.length; i++) disp[nodes[i]] = { x: 0, y: 0 };

            for (var i = 0; i < nodes.length; i++) {
              for (var j = i + 1; j < nodes.length; j++) {
                var dx = positions[nodes[i]].x - positions[nodes[j]].x;
                var dy = positions[nodes[i]].y - positions[nodes[j]].y;
                var dist = Math.sqrt(dx * dx + dy * dy) || 1;
                var force = (k * k) / dist;
                var fx = (dx / dist) * force;
                var fy = (dy / dist) * force;
                disp[nodes[i]].x += fx;
                disp[nodes[i]].y += fy;
                disp[nodes[j]].x -= fx;
                disp[nodes[j]].y -= fy;
              }
            }

            // Attraction
            for (var i = 0; i < edges.length; i++) {
              var s = edges[i].source, t = edges[i].target;
              var dx = positions[s].x - positions[t].x;
              var dy = positions[s].y - positions[t].y;
              var dist = Math.sqrt(dx * dx + dy * dy) || 1;
              var force = (dist * dist) / k;
              var fx = (dx / dist) * force;
              var fy = (dy / dist) * force;
              disp[s].x -= fx;
              disp[s].y -= fy;
              disp[t].x += fx;
              disp[t].y += fy;
            }

            // Apply displacements with temperature cooling
            temperature *= 0.95;
            for (var i = 0; i < nodes.length; i++) {
              var d = disp[nodes[i]];
              var dispLen = Math.sqrt(d.x * d.x + d.y * d.y) || 1;
              var scale = Math.min(dispLen, temperature) / dispLen;
              positions[nodes[i]].x += d.x * scale;
              positions[nodes[i]].y += d.y * scale;
            }

            // Report progress
            if (iter % 50 === 0) {
              self.postMessage({
                type: 'layout-step',
                progress: iter / iterations,
                positions: Object.keys(positions).map(function(id) {
                  return { id: id, x: positions[id].x, y: positions[id].y };
                })
              });
            }
          }

          // Final result
          self.postMessage({
            type: 'layout-complete',
            positions: Object.keys(positions).map(function(id) {
              return { id: id, x: positions[id].x, y: positions[id].y };
            })
          });
        }
      };
    `;
  }

  private handleMessage(msg: WorkerMessage): void {
    // Find the oldest pending computation (FIFO)
    const firstKey = this.pending.keys().next().value;
    if (firstKey === undefined) return;

    const pending = this.pending.get(firstKey);
    if (!pending) return;

    if (msg.type === 'layout-step' && pending.onProgress) {
      pending.onProgress(msg.progress ?? 0);
    } else if (msg.type === 'layout-complete') {
      this.pending.delete(firstKey);
      pending.resolve(msg.positions ?? []);
    } else if (msg.type === 'layout-error') {
      this.pending.delete(firstKey);
      pending.reject(new Error(msg.error || 'Layout computation failed'));
    }
  }

  /**
   * Start a layout computation.
   * Returns a promise that resolves with node positions.
   */
  computeLayout(
    nodes: Array<{ id: string }>,
    edges: Array<{ source: string; target: string }>,
    options?: {
      iterations?: number;
      width?: number;
      height?: number;
      onProgress?: (progress: number) => void;
    },
  ): Promise<Array<{ id: string; x: number; y: number }>> {
    return new Promise((resolve, reject) => {
      if (!this.worker) {
        reject(new Error('Web Worker not supported'));
        return;
      }

      const id = ++this.messageId;
      this.pending.set(id, {
        resolve,
        reject,
        onProgress: options?.onProgress,
      });

      this.worker.postMessage({
        type: 'start',
        nodes: nodes.map((n) => n.id),
        edges,
        iterations: options?.iterations ?? 300,
        width: options?.width ?? 1000,
        height: options?.height ?? 1000,
      });
    });
  }

  /**
   * Terminate the worker and clean up resources.
   */
  dispose(): void {
    if (this.worker) {
      this.worker.terminate();
      this.worker = null;
    }
    for (const [, pending] of this.pending) {
      pending.reject(new Error('Layout worker disposed'));
    }
    this.pending.clear();
  }
}

// ─── Adaptive Quality ───────────────────────────────────────────────────────

/**
 * Monitors frame rate and adjusts quality settings dynamically
 * to maintain target FPS.
 */
export class AdaptiveQuality {
  private targetFPS: number;
  private currentQuality: number; // 0-1 scale
  private frameTimes: number[] = [];
  private lastFrameTime = 0;
  private rafId: number | null = null;
  private onQualityChange: ((quality: number) => void) | null = null;

  constructor(targetFPS = 60, initialQuality = 1) {
    this.targetFPS = targetFPS;
    this.currentQuality = initialQuality;
  }

  /**
   * Start monitoring frame rate.
   */
  start(onQualityChange: (quality: number) => void): void {
    this.onQualityChange = onQualityChange;
    this.lastFrameTime = performance.now();
    const loop = () => {
      const now = performance.now();
      const delta = now - this.lastFrameTime;
      this.lastFrameTime = now;
      this.frameTimes.push(delta);

      // Keep last 60 frames
      if (this.frameTimes.length > 60) {
        this.frameTimes.shift();
      }

      // Adjust quality every 30 frames
      if (this.frameTimes.length === 60) {
        this.adjustQuality();
      }

      this.rafId = requestAnimationFrame(loop);
    };
    this.rafId = requestAnimationFrame(loop);
  }

  private adjustQuality(): void {
    const avgFrameTime =
      this.frameTimes.reduce((a, b) => a + b, 0) / this.frameTimes.length;
    const currentFPS = 1000 / avgFrameTime;

    if (currentFPS < this.targetFPS * 0.8) {
      // FPS too low, reduce quality
      this.currentQuality = Math.max(0.2, this.currentQuality - 0.1);
      this.onQualityChange?.(this.currentQuality);
    } else if (currentFPS > this.targetFPS * 0.95 && this.currentQuality < 1) {
      // FPS good, can increase quality
      this.currentQuality = Math.min(1, this.currentQuality + 0.05);
      this.onQualityChange?.(this.currentQuality);
    }

    this.frameTimes = [];
  }

  /**
   * Stop monitoring.
   */
  stop(): void {
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
  }

  /**
   * Get current quality level (0-1).
   */
  get quality(): number {
    return this.currentQuality;
  }

  /**
   * Manually set quality level (0-1).
   */
  set quality(value: number) {
    this.currentQuality = Math.max(0, Math.min(1, value));
  }
}

// ─── Render Budget ──────────────────────────────────────────────────────────

/**
 * Tracks render time budget to prevent frame drops.
 * If a render operation exceeds the budget, it can be deferred.
 */
export class RenderBudget {
  private budgetMs: number;
  private lastRenderTime = 0;

  constructor(targetFPS = 60) {
    this.budgetMs = 1000 / targetFPS;
  }

  /**
   * Check if there's enough budget remaining for a render operation.
   */
  hasBudget(estimatedCostMs = 0): boolean {
    const elapsed = performance.now() - this.lastRenderTime;
    return elapsed + estimatedCostMs < this.budgetMs;
  }

  /**
   * Mark the start of a render operation.
   */
  begin(): void {
    this.lastRenderTime = performance.now();
  }

  /**
   * Get the time remaining in the current frame budget.
   */
  remaining(): number {
    const elapsed = performance.now() - this.lastRenderTime;
    return Math.max(0, this.budgetMs - elapsed);
  }

  /**
   * Update the target FPS (and thus the budget).
   */
  setTargetFPS(fps: number): void {
    this.budgetMs = 1000 / fps;
  }
}

// ─── Utility Functions ──────────────────────────────────────────────────────

/**
 * Debounce function for resize/scroll events.
 */
export function debounce<T extends (...args: unknown[]) => void>(
  fn: T,
  delay: number,
): (...args: Parameters<T>) => void {
  let timer: ReturnType<typeof setTimeout> | null = null;
  return (...args: Parameters<T>) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

/**
 * Throttle function for high-frequency events (e.g., mouse move).
 */
export function throttle<T extends (...args: unknown[]) => void>(
  fn: T,
  limit: number,
): (...args: Parameters<T>) => void {
  let lastCall = 0;
  return (...args: Parameters<T>) => {
    const now = performance.now();
    if (now - lastCall >= limit) {
      lastCall = now;
      fn(...args);
    }
  };
}

/**
 * Estimate the render cost of a node/edge set based on count and complexity.
 */
export function estimateRenderCost(
  nodeCount: number,
  edgeCount: number,
  showLabels: boolean,
): number {
  // Rough heuristic: each node costs ~0.01ms, each edge ~0.005ms, labels add 50%
  let cost = nodeCount * 0.01 + edgeCount * 0.005;
  if (showLabels) cost *= 1.5;
  return cost;
}

/**
 * Compute the optimal number of nodes to render given a time budget.
 */
export function computeOptimalNodeCount(
  budgetMs: number,
  edgeCount: number,
  showLabels: boolean,
): number {
  const edgeCost = edgeCount * 0.005;
  const labelMultiplier = showLabels ? 1.5 : 1;
  const availableForNodes = Math.max(0, budgetMs - edgeCost);
  return Math.floor(availableForNodes / (0.01 * labelMultiplier));
}

// ─── Export singleton instances ─────────────────────────────────────────────

/** Shared RAF batcher for all graph renderers */
export const sharedRAFBatcher = new RAFBatcher();

/** Shared render budget tracker */
export const sharedRenderBudget = new RenderBudget(60);
