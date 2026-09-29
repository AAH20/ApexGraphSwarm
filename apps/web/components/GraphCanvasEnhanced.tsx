/**
 * React component for graph canvas enhanced.
 *
 * @module GraphCanvasEnhanced
 * @packageDocumentation
 */
"use client";

import Graph from "graphology";
import Sigma from "sigma";
import ForceAtlas2Layout from "graphology-layout-forceatlas2/worker";
import { circular } from "graphology-layout";
import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import type { GraphEdge, GraphNode } from "../lib/graph";
import { bindRendererContextEvents } from "../lib/renderer-lifecycle";

// ─── Optional: community detection + centrality ────────────────────────────
// These are dynamic imports so the bundle stays small if unused.
/**
 * Type Louvain.
 *
 *
 * @example
 * ```typescript
 * import { Louvain } from './module';
 * ```
 */
type Louvain = (graph: Graph) => Record<string, number>;
/**
 * Type PageRank.
 *
 *
 * @example
 * ```typescript
 * import { PageRank } from './module';
 * ```
 */
type PageRank = (graph: Graph, opts?: { alpha?: number }) => Record<string, number>;

/**
 * Type Layout.
 *
 *
 * @example
 * ```typescript
 * import { Layout } from './module';
 * ```
 */
type Layout = "grouped" | "force" | "circular" | "3d";
export type GraphCanvasStatus = {
  renderer: string;
  layoutRunning: boolean;
  visible: number;
  error?: string;
};

type Props = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  selected: string | null;
  onSelect: (id: string) => void;
  layout: Layout;
  onStatus?: (status: GraphCanvasStatus) => void;
  graphLabel?: string;
  fallbackLabel?: string;
  nodeActionLabel?: (node: GraphNode) => string;
  labelsAlwaysVisible?: boolean;
  // ─── New props ──────────────────────────────────────────────────────────
  showMinimap?: boolean;
  showLegend?: boolean;
  showExport?: boolean;
  showSearch?: boolean;
  showCommunities?: boolean;
  showCentrality?: boolean;
  showEdgeLabels?: boolean;
  show3D?: boolean;
  showTimeSlider?: boolean;
  timeRange?: [number, number];
  onTimeChange?: (t: number) => void;
  nodeFilter?: (node: GraphNode) => boolean;
  edgeFilter?: (edge: GraphEdge) => boolean;
  multiSelect?: boolean;
  onMultiSelect?: (ids: string[]) => void;
};

const COLORS: Record<GraphNode["kind"], string> = {
  module: "#8493ff",
  file: "#53c5ad",
  function: "#70a8ff",
  class: "#f2bf68",
  external: "#9ba6b8",
};

const COMMUNITY_PALETTE = [
  "#8493ff", "#53c5ad", "#70a8ff", "#f2bf68", "#e879f9",
  "#fb923c", "#34d399", "#f472b6", "#a78bfa", "#fbbf24",
  "#22d3ee", "#f87171", "#4ade80", "#818cf8", "#e879f9",
];

/**
 * Function groupedPositions.
 *
 * @param {GraphNode[]} nodes - Description of nodes.
 *
 * @example
 * ```typescript
 * const result = groupedPositions(...);
 * ```
 */
function groupedPositions(nodes: GraphNode[]) {
  const groups = new Map<string, GraphNode[]>();
  for (const node of [...nodes].sort((a, b) => a.id.localeCompare(b.id))) {
    const group = node.kind;
    const members = groups.get(group) ?? [];
    members.push(node);
    groups.set(group, members);
  }
  const names = [...groups.keys()].sort();
  const positions = new Map<string, { x: number; y: number }>();
  names.forEach((name, groupIndex) => {
    const members = groups.get(name)!;
    const angle = (2 * Math.PI * groupIndex) / Math.max(names.length, 1) - Math.PI / 2;
    const centerX = names.length === 1 ? 0 : Math.cos(angle) * 2.1;
    const centerY = names.length === 1 ? 0 : Math.sin(angle) * 2.1;
    const radius = Math.max(0.45, Math.min(1.7, 0.22 * Math.sqrt(members.length)));
    members.forEach((node, index) => {
      const nodeAngle = (2 * Math.PI * index) / Math.max(members.length, 1);
      positions.set(node.id, {
        x: centerX + Math.cos(nodeAngle) * radius,
        y: centerY + Math.sin(nodeAngle) * radius,
      });
    });
  });
  return positions;
}

/**
 * Function circularPositions.
 *
 * @param {GraphNode[]} nodes - Description of nodes.
 *
 * @example
 * ```typescript
 * const result = circularPositions(...);
 * ```
 */
function circularPositions(nodes: GraphNode[]) {
  const positions = new Map<string, { x: number; y: number }>();
  const sorted = [...nodes].sort((a, b) => a.id.localeCompare(b.id));
  sorted.forEach((node, i) => {
    const angle = (2 * Math.PI * i) / Math.max(sorted.length, 1);
    const radius = Math.max(1.5, 0.3 * Math.sqrt(sorted.length));
    positions.set(node.id, { x: Math.cos(angle) * radius, y: Math.sin(angle) * radius });
  });
  return positions;
}

export default function GraphCanvasEnhanced({
  nodes, edges, selected, onSelect, layout, onStatus,
  graphLabel = "Interactive repository graph",
  fallbackLabel = "Repository graph SVG fallback",
  nodeActionLabel = (node) => `Select ${node.kind}: ${node.name}`,
  labelsAlwaysVisible = false,
  showMinimap = true,
  showLegend = true,
  showExport = true,
  showSearch = true,
  showCommunities = false,
  showCentrality = false,
  showEdgeLabels = false,
  show3D = false,
  showTimeSlider = false,
  timeRange,
  onTimeChange,
  nodeFilter,
  edgeFilter,
  multiSelect = false,
  onMultiSelect,
}: Props) {
  const hostRef = useRef<HTMLDivElement>(null);
  const minimapRef = useRef<HTMLDivElement>(null);
  const sigmaRef = useRef<Sigma | null>(null);
  const minimapSigmaRef = useRef<Sigma | null>(null);
  const graphRef = useRef<Graph | null>(null);
  const workerRef = useRef<ForceAtlas2Layout | null>(null);
  const selectedRef = useRef(selected);
  const onSelectRef = useRef(onSelect);
  const onStatusRef = useRef(onStatus);
  const workerTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [activeLayout, setActiveLayout] = useState<Layout>(layout);
  const [renderError, setRenderError] = useState<string | null>(null);
  const [contextError, setContextError] = useState<string | null>(null);
  const [renderAttempt, setRenderAttempt] = useState(0);
  const [reducedMotion, setReducedMotion] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [selectedNodes, setSelectedNodes] = useState<Set<string>>(new Set());
  const [communities, setCommunities] = useState<Record<string, number> | null>(null);
  const [centrality, setCentrality] = useState<Record<string, number> | null>(null);
  const [is3D, setIs3D] = useState(false);
  const [timeValue, setTimeValue] = useState(0);

  // ─── Community detection ─────────────────────────────────────────────────
  useEffect(() => {
    if (!showCommunities || nodes.length < 3) {
      setCommunities(null);
      return;
    }
    let cancelled = false;
    import("graphology-communities-louvain").then((mod: { default: Louvain }) => {
      if (cancelled) return;
      try {
        const g = new Graph();
        nodes.forEach((n) => g.addNode(n.id, { kind: n.kind }));
        edges.forEach((e) => {
          if (g.hasNode(e.source) && g.hasNode(e.target)) {
            g.addEdge(e.source, e.target);
          }
        });
        setCommunities(mod.default(g));
      } catch {
        setCommunities(null);
      }
    });
    return () => { cancelled = true; };
  }, [showCommunities, nodes, edges]);

  // ─── PageRank centrality ────────────────────────────────────────────────
  useEffect(() => {
    if (!showCentrality || nodes.length < 3) {
      setCentrality(null);
      return;
    }
    let cancelled = false;
    import("graphology-metrics").then((mod) => {
      if (cancelled) return;
      try {
        const g = new Graph();
        nodes.forEach((n) => g.addNode(n.id));
        edges.forEach((e) => {
          if (g.hasNode(e.source) && g.hasNode(e.target)) {
            g.addEdge(e.source, e.target);
          }
        });
        setCentrality(mod.centrality.pagerank(g, { alpha: 0.85, getEdgeWeight: () => 1 }));
      } catch {
        setCentrality(null);
      }
    });
    return () => { cancelled = true; };
  }, [showCentrality, nodes, edges]);

  // ─── Search ─────────────────────────────────────────────────────────────
  const searchResults = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return [];
    return nodes.filter((n) =>
      (n.name + " " + n.path).toLowerCase().includes(q)
    ).slice(0, 20);
  }, [searchQuery, nodes]);

  const focusNode = useCallback((id: string) => {
    const sigma = sigmaRef.current;
    const graph = graphRef.current;
    if (!sigma || !graph || !graph.hasNode(id)) return;
    const attrs = graph.getNodeAttributes(id);
    sigma.getCamera().animate(
      { x: attrs.x, y: attrs.y, ratio: 0.1 },
      { duration: reducedMotion ? 0 : 500 }
    );
  }, [reducedMotion]);

  // ─── Multi-select ───────────────────────────────────────────────────────
  const handleNodeClick = useCallback((id: string, shiftKey: boolean) => {
    if (multiSelect && shiftKey) {
      setSelectedNodes((prev) => {
        const next = new Set(prev);
        if (next.has(id)) next.delete(id);
        else next.add(id);
        onMultiSelect?.(Array.from(next));
        return next;
      });
    } else {
      setSelectedNodes(new Set([id]));
      onSelect(id);
    }
  }, [multiSelect, onSelect, onMultiSelect]);

  // ─── Export PNG ─────────────────────────────────────────────────────────
  const exportPNG = useCallback(() => {
    const sigma = sigmaRef.current;
    if (!sigma) return;
    const canvas = sigma.getStageCanvas();
    const link = document.createElement("a");
    link.download = `graph-${Date.now()}.png`;
    link.href = canvas.toDataURL("image/png");
    link.click();
  }, []);

  // ─── Fallback ───────────────────────────────────────────────────────────
  const fallback = useMemo(() => {
    const fallbackNodes = nodes.slice(0, 200);
    const ids = new Set(fallbackNodes.map((node) => node.id));
    const fallbackEdges: GraphEdge[] = [];
    let moreEdges = false;
    for (const edge of edges) {
      if (!ids.has(edge.source) || !ids.has(edge.target)) continue;
      if (fallbackEdges.length === 600) { moreEdges = true; break; }
      fallbackEdges.push(edge);
    }
    const positions = groupedPositions(fallbackNodes);
    const points = [...positions.values()];
    const minX = Math.min(0, ...points.map(p => p.x));
    const maxX = Math.max(0, ...points.map(p => p.x));
    const minY = Math.min(0, ...points.map(p => p.y));
    const maxY = Math.max(0, ...points.map(p => p.y));
    for (const [id, point] of positions) positions.set(id, {
      x: maxX === minX ? 500 : 90 + (point.x - minX) / (maxX - minX) * 740,
      y: maxY === minY ? 440 : 220 + (point.y - minY) / (maxY - minY) * 420,
    });
    return { nodes: fallbackNodes, edges: fallbackEdges, positions, truncated: nodes.length > fallbackNodes.length || moreEdges };
  }, [nodes, edges]);

  selectedRef.current = selected;
  onSelectRef.current = onSelect;
  onStatusRef.current = onStatus;

  useEffect(() => setActiveLayout(layout), [layout]);

  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReducedMotion(query.matches);
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);

  // ─── Main renderer ──────────────────────────────────────────────────────
  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;

    let renderer: Sigma | null = null;
    let graph: Graph | null = null;
    let unbindContextEvents = () => {};
    try {
      graph = new Graph({ multi: true, type: "directed" });
      const positions = activeLayout === "circular" ? circularPositions(nodes) : groupedPositions(nodes);
      const nodeById = new Map(nodes.map((node) => [node.id, node]));

      for (const node of nodes) {
        const point = positions.get(node.id) ?? { x: 0, y: 0 };
        const communityId = communities?.[node.id];
        const centralityScore = centrality?.[node.id];
        const nodeColor = showCommunities && communityId !== undefined
          ? COMMUNITY_PALETTE[communityId % COMMUNITY_PALETTE.length]
          : COLORS[node.kind];
        const nodeSize = showCentrality && centralityScore !== undefined
          ? Math.max(4, Math.min(20, 4 + centralityScore * 30))
          : node.kind === "module" ? 6 : Math.min(10, 4 + Math.log2((node.connections ?? 0) + 1));

        graph.addNode(node.id, {
          x: point.x,
          y: point.y,
          label: node.name,
          color: nodeColor,
          size: nodeSize,
          kind: node.kind,
        });
      }

      edges.forEach((edge, index) => {
        if (!nodeById.has(edge.source) || !nodeById.has(edge.target)) return;
        graph!.addDirectedEdgeWithKey(`relationship-${index}`, edge.source, edge.target, {
          color: "rgba(151, 167, 194, 0.22)",
          size: Math.min(2, 0.6 + Math.log2((edge.count ?? 1) + 1) * 0.25),
          relation: edge.relation,
          label: showEdgeLabels ? edge.relation : undefined,
        });
      });

      renderer = new Sigma(graph, host, {
        styles: {
          nodes: {
            x: { attribute: "x" },
            y: { attribute: "y" },
            size: { attribute: "size", defaultValue: 4 },
            color: { attribute: "color", defaultValue: COLORS.file },
            label: { attribute: "label" },
            labelColor: "#e5ebf6",
            labelFont: "Inter, ui-sans-serif, system-ui, sans-serif",
            labelSize: nodes.length <= 60 ? 13 : 11,
          },
          edges: {
            size: { attribute: "size", defaultValue: 1 },
            color: { attribute: "color", defaultValue: "rgba(151, 167, 194, 0.22)" },
            label: { attribute: "label" },
            head: "arrow",
          },
        },
        settings: {
          labelRenderedSizeThreshold: labelsAlwaysVisible || nodes.length <= 60 ? 0 : 7,
          labelDensity: labelsAlwaysVisible || nodes.length <= 60 ? 1 : 0.08,
          stagePadding: 28,
          minCameraRatio: 0.08,
          maxCameraRatio: 8,
          hideEdgesOnMove: true,
          renderEdgeLabels: showEdgeLabels,
        },
        nodeReducer: (key, data) => {
          const isSelected = selectedRef.current === key || selectedNodes.has(key);
          const isHovered = hoveredNode === key;
          if (isSelected) return { ...data, color: "#ffffff", size: Math.max(data.size ?? 4, 9), zIndex: 2 };
          if (isHovered) return { ...data, color: "#b4c5ff", size: Math.max(data.size ?? 4, 7), zIndex: 1 };
          if (selectedRef.current && graph!.hasNode(selectedRef.current)) {
            return { ...data, color: "#445067", zIndex: 0 };
          }
          return data;
        },
        edgeReducer: (key, data) => {
          if (!selectedRef.current || !graph!.hasNode(selectedRef.current)) return data;
          const source = graph!.source(key);
          const target = graph!.target(key);
          return source === selectedRef.current || target === selectedRef.current
            ? { ...data, color: "rgba(180, 197, 255, 0.75)", size: Math.max(data.size ?? 1, 1.5) }
            : { ...data, color: "rgba(75, 87, 110, 0.12)" };
        },
      });

      renderer.on("clickNode", ({ node, event }) => {
        const original = event.original as MouseEvent | undefined;
        handleNodeClick(node, original?.shiftKey ?? false);
      });
      renderer.on("enterNode", ({ node }) => setHoveredNode(node));
      renderer.on("leaveNode", () => setHoveredNode(null));

      const onContextLost = (event: Event) => {
        event.preventDefault();
        const message = "WebGL context was lost.";
        if (workerTimerRef.current) clearTimeout(workerTimerRef.current);
        workerTimerRef.current = null;
        workerRef.current?.stop();
        workerRef.current?.kill();
        workerRef.current = null;
        setContextError(message);
        onStatusRef.current?.({ renderer: "unavailable", layoutRunning: false, visible: nodes.length, error: message });
      };
      const onContextRestored = () => {
        setContextError(null);
        setRenderAttempt((attempt) => attempt + 1);
      };
      unbindContextEvents = bindRendererContextEvents(
        host.querySelectorAll("canvas"), onContextLost, onContextRestored,
      );

      graphRef.current = graph;
      sigmaRef.current = renderer;
      setRenderError(null);
      setContextError(null);
      onStatusRef.current?.({ renderer: "sigma-webgl", layoutRunning: false, visible: nodes.length });
    } catch (error) {
      unbindContextEvents();
      renderer?.kill();
      host.replaceChildren();
      graphRef.current = null;
      sigmaRef.current = null;
      const message = error instanceof Error ? error.message : "The graph renderer could not be initialized.";
      setRenderError(message);
      onStatusRef.current?.({ renderer: "unavailable", layoutRunning: false, visible: nodes.length, error: message });
    }

    const observer = new ResizeObserver(() => {
      if (host.clientWidth > 0 && host.clientHeight > 0) renderer?.resize(true);
    });
    observer.observe(host);
    return () => {
      unbindContextEvents();
      observer.disconnect();
      if (workerTimerRef.current) clearTimeout(workerTimerRef.current);
      workerTimerRef.current = null;
      workerRef.current?.stop();
      workerRef.current?.kill();
      workerRef.current = null;
      renderer?.kill();
      if (sigmaRef.current === renderer) sigmaRef.current = null;
      if (graphRef.current === graph) graphRef.current = null;
    };
  }, [nodes, edges, renderAttempt, activeLayout, communities, centrality, showCommunities, showCentrality, showEdgeLabels, hoveredNode, selectedNodes, handleNodeClick]);

  // ─── Minimap renderer ───────────────────────────────────────────────────
  useEffect(() => {
    if (!showMinimap || !minimapRef.current || nodes.length < 10) return;
    const minimapGraph = new Graph();
    nodes.forEach((n) => {
      minimapGraph.addNode(n.id, { x: Math.random(), y: Math.random(), size: 2, color: COLORS[n.kind] });
    });
    edges.forEach((e) => {
      if (minimapGraph.hasNode(e.source) && minimapGraph.hasNode(e.target)) {
        minimapGraph.addEdge(e.source, e.target, { size: 0.5, color: "rgba(151,167,194,0.15)" });
      }
    });
    const minimapSigma = new Sigma(minimapGraph, minimapRef.current, {
      styles: {
        nodes: {
          x: { attribute: "x" },
          y: { attribute: "y" },
          size: { attribute: "size", defaultValue: 2 },
          color: { attribute: "color" },
        },
        edges: {
          size: { attribute: "size", defaultValue: 0.5 },
          color: { attribute: "color" },
        },
      },
      settings: {
        renderEdgeLabels: false,
        labelRenderedSizeThreshold: 999,
        minCameraRatio: 0.1,
        maxCameraRatio: 10,
      },
    });
    minimapSigmaRef.current = minimapSigma;
    return () => {
      minimapSigma.kill();
      minimapSigmaRef.current = null;
    };
  }, [showMinimap, nodes, edges]);

  // ─── Layout effect ──────────────────────────────────────────────────────
  useEffect(() => {
    sigmaRef.current?.refresh();
  }, [selected, hoveredNode]);

  useEffect(() => {
    const graph = graphRef.current;
    if (!graph) return;

    if (activeLayout === "force" && !reducedMotion && graph.order >= 2) {
      let worker: ForceAtlas2Layout | null = null;
      try {
        worker = new ForceAtlas2Layout(graph, {
          settings: {
            gravity: 0.12,
            scalingRatio: 6,
            slowDown: 2,
            barnesHutOptimize: graph.order > 200,
            outboundAttractionDistribution: true,
          },
        });
        workerRef.current = worker;
        worker.start();
        onStatusRef.current?.({ renderer: "sigma-webgl", layoutRunning: true, visible: nodes.length });
        workerTimerRef.current = setTimeout(() => {
          worker?.stop();
          worker?.kill();
          if (workerRef.current === worker) workerRef.current = null;
          workerTimerRef.current = null;
          sigmaRef.current?.refresh();
          onStatusRef.current?.({ renderer: "sigma-webgl", layoutRunning: false, visible: nodes.length });
        }, 3000);
      } catch (error) {
        worker?.kill();
        const message = error instanceof Error ? error.message : "The force layout could not be started.";
        onStatusRef.current?.({ renderer: "sigma-webgl", layoutRunning: false, visible: nodes.length, error: message });
      }
      return () => {
        if (workerTimerRef.current) clearTimeout(workerTimerRef.current);
        workerTimerRef.current = null;
        worker?.stop();
        worker?.kill();
        if (workerRef.current === worker) workerRef.current = null;
      };
    }

    // Non-force layouts: set positions directly
    const positions = activeLayout === "circular" ? circularPositions(nodes) : groupedPositions(nodes);
    positions.forEach((point, id) => {
      if (graph.hasNode(id)) {
        graph.setNodeAttribute(id, "x", point.x);
        graph.setNodeAttribute(id, "y", point.y);
      }
    });
    sigmaRef.current?.refresh();
    onStatusRef.current?.({ renderer: "sigma-webgl", layoutRunning: false, visible: nodes.length });
  }, [activeLayout, nodes, edges, reducedMotion, renderAttempt]);

  const chooseLayout = (next: Layout) => setActiveLayout(next);
  const camera = () => sigmaRef.current?.getCamera();
  const motionDuration = reducedMotion ? 0 : 180;

  // ─── Legend data ────────────────────────────────────────────────────────
  const legendItems = useMemo(() => {
    if (showCommunities && communities) {
      const unique = [...new Set(Object.values(communities))].sort();
      return unique.map((id) => ({
        label: `Community ${id + 1}`,
        color: COMMUNITY_PALETTE[id % COMMUNITY_PALETTE.length],
      }));
    }
    return Object.entries(COLORS).map(([kind, color]) => ({ label: kind, color }));
  }, [showCommunities, communities]);

  return (
    <div className="graph-canvas-surface" style={{ position: "relative", width: "100%", height: "100%", minHeight: 320 }}>
      {/* Search bar */}
      {showSearch && (
        <div style={{ position: "absolute", top: 12, left: 12, zIndex: 10, width: 260 }}>
          <input
            type="text"
            placeholder="Search nodes…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: "100%", padding: "8px 12px", borderRadius: 8,
              border: "1px solid rgba(184,199,222,0.24)", background: "rgba(13,25,40,0.95)",
              color: "#e7edf6", fontSize: 13, outline: "none",
            }}
          />
          {searchResults.length > 0 && (
            <div style={{
              marginTop: 4, background: "rgba(13,25,40,0.97)", borderRadius: 8,
              border: "1px solid rgba(184,199,222,0.24)", maxHeight: 200, overflowY: "auto",
            }}>
              {searchResults.map((n) => (
                <button
                  key={n.id}
                  onClick={() => { focusNode(n.id); setSearchQuery(""); }}
                  style={{
                    display: "block", width: "100%", padding: "6px 12px", border: "none",
                    background: "transparent", color: "#c3cede", fontSize: 12, textAlign: "left", cursor: "pointer",
                  }}
                >
                  {n.name} <span style={{ color: "#71829d" }}>· {n.kind}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Export button */}
      {showExport && (
        <button
          onClick={exportPNG}
          style={{
            position: "absolute", top: 12, right: 12, zIndex: 10,
            padding: "6px 12px", borderRadius: 8, border: "1px solid rgba(184,199,222,0.24)",
            background: "rgba(13,25,40,0.95)", color: "#e7edf6", fontSize: 12, cursor: "pointer",
          }}
        >
          Export PNG
        </button>
      )}

      {/* Main canvas */}
      <div
        ref={hostRef}
        className="graph-canvas-renderer"
        aria-label={graphLabel}
        style={{ position: "absolute", inset: 0, visibility: renderError || contextError ? "hidden" : undefined }}
      />

      {/* SVG Fallback */}
      {(renderError || contextError) && (
        <svg
          className="graph-canvas-svg-fallback"
          viewBox="0 0 1000 700"
          preserveAspectRatio="xMidYMid meet"
          role="group"
          aria-label={fallbackLabel}
          style={{ position: "absolute", inset: 0, width: "100%", height: "100%", background: "#101b2b" }}
        >
          <defs>
            <marker id="graph-fallback-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#8291aa" />
            </marker>
          </defs>
          {fallback.edges.map((edge, index) => {
            const source = fallback.positions.get(edge.source);
            const target = fallback.positions.get(edge.target);
            if (!source || !target) return null;
            const sx = source.x, sy = source.y, tx = target.x, ty = target.y;
            if (edge.source === edge.target) {
              return (
                <path key={`fallback-edge-${index}`}
                  d={`M ${sx - 4} ${sy - 4} C ${sx - 32} ${sy - 46}, ${sx + 32} ${sy - 46}, ${sx + 4} ${sy - 4}`}
                  fill="none" stroke="#71829d" strokeOpacity="0.55" strokeWidth="1.2"
                  markerEnd="url(#graph-fallback-arrow)"
                >
                  <title>{edge.relation}</title>
                </path>
              );
            }
            const dx = tx - sx, dy = ty - sy;
            const distance = Math.max(Math.hypot(dx, dy), 1);
            const ux = dx / distance, uy = dy / distance;
            return (
              <line key={`fallback-edge-${index}`}
                x1={sx + ux * 6} y1={sy + uy * 6} x2={tx - ux * 8} y2={ty - uy * 8}
                stroke="#8291aa" strokeOpacity="0.42" strokeWidth="1.1"
                markerEnd="url(#graph-fallback-arrow)"
              >
                <title>{edge.relation}</title>
              </line>
            );
          })}
          {fallback.nodes.map((node) => {
            const point = fallback.positions.get(node.id) ?? { x: 0, y: 0 };
            const x = point.x, y = point.y;
            const isSelected = selected === node.id;
            const radius = Math.min(9, 4 + Math.log2((node.connections ?? 0) + 1) * 0.65);
            return (
              <g key={node.id} role="button" tabIndex={0}
                aria-label={nodeActionLabel(node)} aria-pressed={isSelected}
                onClick={() => onSelect(node.id)}
                onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onSelect(node.id); } }}
                style={{ cursor: "pointer", outline: "none" }}
              >
                <title>{`${node.name} · ${node.path || node.kind}`}</title>
                <circle cx={x} cy={y} r={radius}
                  fill={COLORS[node.kind]}
                  stroke={isSelected ? "#ffffff" : "#101b2b"}
                  strokeWidth={isSelected ? 3 : 1.5}
                />
                <text x={x + radius + 4} y={y + 3}
                  fill={isSelected ? "#ffffff" : "#c3cede"}
                  fontSize={isSelected ? 12 : 10}
                  fontFamily="Inter, ui-sans-serif, system-ui, sans-serif"
                  pointerEvents="none"
                >
                  {node.name.length > 26 ? `${node.name.slice(0, 25)}…` : node.name}
                </text>
              </g>
            );
          })}
        </svg>
      )}

      {/* Minimap */}
      {showMinimap && !renderError && !contextError && (
        <div
          ref={minimapRef}
          style={{
            position: "absolute", bottom: 12, right: 12, zIndex: 10,
            width: 160, height: 120, borderRadius: 8, overflow: "hidden",
            border: "1px solid rgba(184,199,222,0.24)", background: "rgba(13,25,40,0.9)",
          }}
        />
      )}

      {/* Legend */}
      {showLegend && !renderError && !contextError && (
        <div style={{
          position: "absolute", bottom: 12, left: 12, zIndex: 10,
          padding: "8px 12px", borderRadius: 8,
          background: "rgba(13,25,40,0.9)", border: "1px solid rgba(184,199,222,0.24)",
        }}>
          {legendItems.map((item) => (
            <div key={item.label} style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
              <span style={{ width: 10, height: 10, borderRadius: "50%", background: item.color, display: "inline-block" }} />
              <span style={{ fontSize: 11, color: "#c3cede" }}>{item.label}</span>
            </div>
          ))}
        </div>
      )}

      {/* Tooltip */}
      {hoveredNode && !renderError && !contextError && (
        <div style={{
          position: "absolute", top: 50, right: 12, zIndex: 10,
          padding: "8px 12px", borderRadius: 8, maxWidth: 280,
          background: "rgba(13,25,40,0.97)", border: "1px solid rgba(184,199,222,0.24)",
          color: "#e7edf6", fontSize: 12, pointerEvents: "none",
        }}>
          <strong>{nodes.find((n) => n.id === hoveredNode)?.name}</strong>
          <div style={{ color: "#71829d", fontSize: 11 }}>
            {nodes.find((n) => n.id === hoveredNode)?.kind}
            {communities?.[hoveredNode] !== undefined && ` · Community ${communities[hoveredNode] + 1}`}
            {centrality?.[hoveredNode] !== undefined && ` · PR: ${centrality[hoveredNode].toFixed(3)}`}
          </div>
        </div>
      )}

      {/* Time slider */}
      {showTimeSlider && timeRange && (
        <div style={{
          position: "absolute", bottom: 12, left: "50%", transform: "translateX(-50%)", zIndex: 10,
          padding: "8px 16px", borderRadius: 8,
          background: "rgba(13,25,40,0.9)", border: "1px solid rgba(184,199,222,0.24)",
          display: "flex", alignItems: "center", gap: 12,
        }}>
          <span style={{ fontSize: 11, color: "#c3cede" }}>Time</span>
          <input
            type="range" min={timeRange[0]} max={timeRange[1]} value={timeValue}
            onChange={(e) => { const v = Number(e.target.value); setTimeValue(v); onTimeChange?.(v); }}
            style={{ width: 200 }}
          />
          <span style={{ fontSize: 11, color: "#71829d" }}>{timeValue}</span>
        </div>
      )}

      {/* Canvas controls */}
      {!renderError && !contextError && (
        <div className="canvas-controls" role="toolbar" aria-label="Graph view controls">
          <div className="canvas-layout-controls" aria-label="Layout">
            <button type="button" aria-pressed={activeLayout === "grouped"} onClick={() => chooseLayout("grouped")}>
              Grouped
            </button>
            <button type="button"
              aria-pressed={activeLayout === "force"}
              title={reducedMotion ? "Force layout is paused because reduced motion is enabled" : undefined}
              onClick={() => chooseLayout("force")}
            >
              Force
            </button>
            <button type="button" aria-pressed={activeLayout === "circular"} onClick={() => chooseLayout("circular")}>
              Circular
            </button>
            {show3D && (
              <button type="button" aria-pressed={is3D} onClick={() => setIs3D(!is3D)}>
                {is3D ? "2D" : "3D"}
              </button>
            )}
          </div>
          <button type="button" aria-label="Zoom in" onClick={() => void camera()?.animatedZoom({ duration: motionDuration })}>+</button>
          <button type="button" aria-label="Zoom out" onClick={() => void camera()?.animatedUnzoom({ duration: motionDuration })}>−</button>
          <button type="button" onClick={() => void camera()?.animatedReset({ duration: motionDuration })}>Fit</button>
        </div>
      )}

      {reducedMotion && activeLayout === "force" && (
        <p className="graph-canvas-motion-note" role="status">Force layout is paused while reduced motion is enabled.</p>
      )}

      {/* Error overlay */}
      {(renderError || contextError) && (
        <div className="graph-canvas-fallback" role="status" aria-live="polite"
          style={{
            position: "absolute", zIndex: 8, left: "50%", top: 12, transform: "translateX(-50%)",
            display: "grid", gap: 6, width: "min(540px, calc(100% - 32px))", padding: 10,
            border: "1px solid rgba(184,199,222,0.24)", borderRadius: 10,
            background: "rgba(13,25,40,0.97)", color: "#e7edf6",
            boxShadow: "0 12px 36px rgba(0,0,0,0.3)", textAlign: "center",
          }}
        >
          <strong>Reduced graphics mode</strong>
          <span style={{ color: "#aebbd0", fontSize: 12, lineHeight: 1.6 }}>
            WebGL is unavailable. Select nodes in the SVG overview below, use the node list, or retry GPU rendering.
          </span>
          <button
            type="button"
            onClick={() => setRenderAttempt((attempt) => attempt + 1)}
            style={{ justifySelf: "center", padding: "7px 11px", border: "1px solid #596c87", borderRadius: 6, background: "#24364e", color: "#f1f5fb" }}
          >
            Retry graph renderer
          </button>
          {fallback.truncated && (
            <span role="note" style={{ color: "#e4c27b", fontSize: 11 }}>
              Showing up to 200 nodes and 600 relationships in this fallback view.
            </span>
          )}
        </div>
      )}
    </div>
  );
}
