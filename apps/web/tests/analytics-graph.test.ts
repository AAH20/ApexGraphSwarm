import assert from 'node:assert/strict';
import test from 'node:test';
import { adaptAnalyticsGraph, analyticsEdgeKey, filterAnalyticsGraph, MAX_ANALYTICS_GRAPH_NODES } from '../lib/analytics-graph';
import type { AnalyticsReport } from '../lib/analytics-types';

const graph: AnalyticsReport['graph'] = {
  nodes: [
    { id: 'tool:a', label: 'model:alpha', kind: 'tool' },
    { id: 'tool:b', label: 'model:beta', kind: 'tool' },
    { id: 'resource:x', label: 'model:reviewer', kind: 'resource' },
    { id: 'resource:y', label: 'filesystem:local', kind: 'resource' },
  ],
  edges: [
    { source: 'tool:a', target: 'resource:x', attempts: 3, knownCostMicrousd: 900 },
    { source: 'tool:b', target: 'resource:x', attempts: 1, knownCostMicrousd: 0 },
    { source: 'tool:a', target: 'resource:y', attempts: 2, knownCostMicrousd: 100 },
    { source: 'missing', target: 'resource:y', attempts: 4, knownCostMicrousd: 50 },
  ],
};

const quality: Pick<AnalyticsReport['quality'], 'unknownCostRows' | 'invalidRows' | 'truncated' | 'selectionKnownCoverage'> = {
  unknownCostRows: 0, invalidRows: 0, truncated: false, selectionKnownCoverage: true,
};

test('adapter maps graph categories and marks observed relationships as aggregated, not dependencies', () => {
  const adapted = adaptAnalyticsGraph(graph, 'live', quality);
  assert.equal(adapted.nodes.find((node) => node.id === 'tool:a')?.kind, 'function');
  assert.equal(adapted.nodes.find((node) => node.id === 'resource:x')?.kind, 'external');
  assert.match(adapted.nodes.find((node) => node.id === 'resource:x')?.summary ?? '', /not a repository dependency/);
  assert.equal(adapted.edges[0].relation, 'observed tool-to-resource usage');
  assert.equal(adapted.edges[0].confidence, 'aggregated');
  assert.equal(adapted.edges[0].count, 3);
  assert.equal(adapted.quality.invalidEdges, 1);
  assert.equal(adapted.quality.evidence, 'aggregated');
});

test('demo relationships are illustrative and source arrays are not mutated', () => {
  const original = JSON.stringify(graph);
  const adapted = adaptAnalyticsGraph(graph, 'demo', quality);
  assert.equal(adapted.quality.evidence, 'illustrative');
  assert.ok(adapted.nodes.every((node) => node.confidence === 'illustrative'));
  assert.ok(adapted.edges.every((edge) => edge.confidence === 'illustrative'));
  assert.equal(JSON.stringify(graph), original);
});

test('category and exact label filters retain only valid edges whose endpoints are visible', () => {
  const adapted = adaptAnalyticsGraph(graph, 'live', quality);
  const filtered = filterAnalyticsGraph(adapted, { category: 'tool', query: 'alpha' });
  assert.deepEqual(filtered.nodes.map((node) => node.id), ['tool:a']);
  assert.equal(filtered.edges.length, 0);
  const resources = filterAnalyticsGraph(adapted, { category: 'resource', query: 'reviewer' });
  assert.deepEqual(resources.nodes.map((node) => node.id), ['resource:x']);
  assert.equal(resources.edges.length, 0);
  const complete = filterAnalyticsGraph(adapted, { query: 'model:' });
  const visibleIds = new Set(complete.nodes.map((node) => node.id));
  assert.ok(complete.edges.every((edge) => visibleIds.has(edge.source) && visibleIds.has(edge.target)));
});

test('selected neighborhood includes only the selected node and direct neighbors', () => {
  const adapted = adaptAnalyticsGraph(graph, 'live', quality);
  const neighborhood = filterAnalyticsGraph(adapted, { selected: 'tool:a', neighborhoodOnly: true });
  assert.deepEqual(new Set(neighborhood.nodes.map((node) => node.id)), new Set(['tool:a', 'resource:x', 'resource:y']));
  assert.ok(neighborhood.edges.every((edge) => edge.source === 'tool:a' || edge.target === 'tool:a'));
});

test('known-cost subtotals remain explicitly incomplete when report has unknown costs', () => {
  const adapted = adaptAnalyticsGraph(graph, 'live', { ...quality, unknownCostRows: 1 });
  const value = adapted.edgeMetrics.get(analyticsEdgeKey('tool:b', 'resource:x'));
  assert.deepEqual(value, { attempts: 1, knownCostMicrousd: 0, complete: false });
  const complete = adaptAnalyticsGraph(graph, 'live', quality).edgeMetrics.get(analyticsEdgeKey('tool:b', 'resource:x'));
  assert.equal(complete?.complete, true);
});

test('node/edge caps are fail-closed and reported as omissions', () => {
  const nodes = Array.from({ length: MAX_ANALYTICS_GRAPH_NODES + 2 }, (_, index) => ({
    id: `tool:${index}`, label: `tool-${index}`, kind: 'tool',
  }));
  const adapted = adaptAnalyticsGraph({ nodes, edges: [
    { source: 'tool:0', target: 'tool:1', attempts: 1, knownCostMicrousd: 1 },
  ] }, 'live', quality);
  assert.equal(adapted.nodes.length, MAX_ANALYTICS_GRAPH_NODES);
  assert.equal(adapted.quality.omittedNodes, 2);
  assert.equal(adapted.edges.length, 0);
  assert.equal(adapted.quality.invalidEdges, 1);
});
