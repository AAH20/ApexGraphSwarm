import type { AnalyticsReport } from './analytics-types';
import type { Evidence, GraphEdge, GraphNode } from './graph';

export type AnalyticsCategory = 'all' | 'tool' | 'resource';
export type AnalyticsGraphMetrics = { attempts: number; knownCostMicrousd: number; complete: boolean };
export type AnalyticsGraphView = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  edgeMetrics: Map<string, AnalyticsGraphMetrics>;
  quality: {
    omittedNodes: number;
    omittedEdges: number;
    invalidNodes: number;
    invalidEdges: number;
    evidence: Evidence;
  };
};

export const MAX_ANALYTICS_GRAPH_NODES = 200;
export const MAX_ANALYTICS_GRAPH_EDGES = 600;
export const analyticsEdgeKey = (source: string, target: string) => JSON.stringify([source, target]);

const safeLabel = (value: unknown): value is string =>
  typeof value === 'string' && value.length > 0 && value.length <= 2000 && !/[\u0000-\u001f\u007f]/.test(value);
const safeCount = (value: unknown): value is number =>
  typeof value === 'number' && Number.isSafeInteger(value) && value >= 0;

/** Convert observed analytics tool/resource usage into the shared graph vocabulary. */
export function adaptAnalyticsGraph(
  graph: AnalyticsReport['graph'],
  source: AnalyticsReport['source'] = 'live',
  coverage?: Partial<Pick<AnalyticsReport['quality'], 'unknownCostRows' | 'invalidRows' | 'truncated' | 'selectionKnownCoverage'>>,
): AnalyticsGraphView {
  const confidence: Evidence = source === 'demo' ? 'illustrative' : 'aggregated';
  const metricComplete = coverage !== undefined && coverage.unknownCostRows === 0 && coverage.invalidRows === 0 &&
    !coverage.truncated && coverage.selectionKnownCoverage === true;
  const nodes: GraphNode[] = [];
  const nodeIds = new Set<string>();
  const nodeKindById = new Map<string, 'tool' | 'resource'>();
  let invalidNodes = 0;
  let omittedNodes = 0;
  const inputNodes = Array.isArray(graph?.nodes) ? graph.nodes : [];
  for (const entry of inputNodes) {
    if (!entry || !safeLabel(entry.id) || !safeLabel(entry.label) ||
        (entry.kind !== 'tool' && entry.kind !== 'resource') || nodeIds.has(entry.id)) {
      invalidNodes += 1;
      continue;
    }
    if (nodes.length >= MAX_ANALYTICS_GRAPH_NODES) {
      omittedNodes += 1;
      continue;
    }
    nodeIds.add(entry.id);
    nodeKindById.set(entry.id, entry.kind);
    const tool = entry.kind === 'tool';
    nodes.push({
      id: entry.id,
      name: entry.label,
      kind: tool ? 'function' : 'external',
      path: `${tool ? 'tool' : 'resource'}:${entry.label}`,
      summary: tool
        ? 'Aggregated analytics tool identifier; not a source-code function inventory.'
        : 'Analytics resource shown in the external visual category only; not a repository dependency.',
      confidence,
      connections: 0,
    });
  }

  const edges: GraphEdge[] = [];
  const edgeMetrics = new Map<string, AnalyticsGraphMetrics>();
  let invalidEdges = 0;
  let omittedEdges = 0;
  const inputEdges = Array.isArray(graph?.edges) ? graph.edges : [];
  for (const entry of inputEdges) {
    if (!entry || !safeLabel(entry.source) || !safeLabel(entry.target) ||
        !nodeIds.has(entry.source) || !nodeIds.has(entry.target) ||
        nodeKindById.get(entry.source) !== 'tool' || nodeKindById.get(entry.target) !== 'resource' ||
        !safeCount(entry.attempts) || entry.attempts < 1 || !safeCount(entry.knownCostMicrousd)) {
      invalidEdges += 1;
      continue;
    }
    const key = analyticsEdgeKey(entry.source, entry.target);
    const current = edgeMetrics.get(key);
    if (current) {
      const attempts = current.attempts + entry.attempts;
      const cost = current.knownCostMicrousd + entry.knownCostMicrousd;
      if (!Number.isSafeInteger(attempts) || !Number.isSafeInteger(cost)) {
        invalidEdges += 1;
        continue;
      }
      current.attempts = attempts;
      current.knownCostMicrousd = cost;
      current.complete = current.complete && metricComplete;
      const prior = edges.find((edge) => analyticsEdgeKey(edge.source, edge.target) === key);
      if (prior) prior.count = attempts;
      continue;
    }
    if (edges.length >= MAX_ANALYTICS_GRAPH_EDGES) {
      omittedEdges += 1;
      continue;
    }
    edgeMetrics.set(key, { attempts: entry.attempts, knownCostMicrousd: entry.knownCostMicrousd, complete: metricComplete });
    edges.push({
      source: entry.source,
      target: entry.target,
      relation: 'observed tool-to-resource usage',
      confidence,
      count: entry.attempts,
    });
  }
  const connectionCounts = new Map<string, number>();
  for (const edge of edges) {
    connectionCounts.set(edge.source, (connectionCounts.get(edge.source) ?? 0) + 1);
    connectionCounts.set(edge.target, (connectionCounts.get(edge.target) ?? 0) + 1);
  }
  for (const node of nodes) node.connections = connectionCounts.get(node.id) ?? 0;

  return { nodes, edges, edgeMetrics, quality: { omittedNodes, omittedEdges, invalidNodes, invalidEdges, evidence: confidence } };
}

export function filterAnalyticsGraph(
  view: Pick<AnalyticsGraphView, 'nodes' | 'edges'>,
  options: { query?: string; category?: AnalyticsCategory; selected?: string | null; neighborhoodOnly?: boolean } = {},
): Pick<AnalyticsGraphView, 'nodes' | 'edges'> {
  const query = (options.query ?? '').trim().toLocaleLowerCase();
  const category = options.category ?? 'all';
  let nodes = view.nodes.filter((node) => {
    const nodeCategory = node.kind === 'function' ? 'tool' : node.kind === 'external' ? 'resource' : null;
    return (category === 'all' || nodeCategory === category) &&
      (!query || `${node.name} ${node.path} ${node.summary}`.toLocaleLowerCase().includes(query));
  });
  let ids = new Set(nodes.map((node) => node.id));
  let edges = view.edges.filter((edge) => ids.has(edge.source) && ids.has(edge.target));

  if (options.neighborhoodOnly && options.selected && ids.has(options.selected)) {
    const selected = options.selected;
    const neighborhood = new Set([selected]);
    for (const edge of edges) {
      if (edge.source === selected) neighborhood.add(edge.target);
      if (edge.target === selected) neighborhood.add(edge.source);
    }
    nodes = nodes.filter((node) => neighborhood.has(node.id));
    ids = new Set(nodes.map((node) => node.id));
    edges = edges.filter((edge) => ids.has(edge.source) && ids.has(edge.target));
  }
  return { nodes, edges };
}
