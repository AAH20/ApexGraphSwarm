import test from 'node:test';
import assert from 'node:assert/strict';
import fc from 'fast-check';
import {parseSnapshot, neighborhood, shortestPath, filterGraph, semanticEdges, indexGraph, type Snapshot, type Filters, type GraphNode, type GraphEdge, type Evidence, type Kind} from '../../lib/graph';

// ---------------------------------------------------------------------------
// Strategies (fast-check v4 API)
// ---------------------------------------------------------------------------

const evidenceArb = fc.constantFrom<Evidence>('parsed', 'observed', 'inferred', 'illustrative', 'aggregated');
const kindArb = fc.constantFrom<Kind>('module', 'file', 'function', 'class', 'external');

const nodeIdArb = fc.string({minLength: 1, maxLength: 32}).map(s => s.replace(/[^a-zA-Z0-9:._-]/g, '_'));

const graphNodeArb: fc.Arbitrary<GraphNode> = fc.record({
  id: nodeIdArb,
  name: fc.string({maxLength: 64}),
  kind: kindArb,
  path: fc.string({maxLength: 64}),
  summary: fc.string({maxLength: 200}),
  confidence: evidenceArb,
  line: fc.option(fc.integer({min: 1, max: 10000}), {nil: undefined}),
  connections: fc.option(fc.nat({max: 1000}), {nil: undefined}),
});

const graphEdgeArb: fc.Arbitrary<GraphEdge> = fc.record({
  source: nodeIdArb,
  target: nodeIdArb,
  relation: fc.string({minLength: 1, maxLength: 40}),
  confidence: evidenceArb,
  line: fc.option(fc.integer({min: 1, max: 10000}), {nil: undefined}),
  count: fc.option(fc.nat({max: 1000}), {nil: undefined}),
});

const snapshotArb: fc.Arbitrary<Snapshot> = fc.record({
  version: fc.integer({min: 1, max: 1000}),
  name: fc.string({maxLength: 100}),
  nodes: fc.uniqueArray(graphNodeArb, {selector: (n: GraphNode) => n.id, maxLength: 30}),
  edges: fc.array(graphEdgeArb, {maxLength: 50}),
  warnings: fc.array(fc.string({maxLength: 200}), {maxLength: 10}),
  truncated: fc.boolean(),
  summary: fc.option(fc.record({unresolved: fc.nat({max: 100})}), {nil: undefined}),
  unresolved: fc.option(fc.array(fc.record({path: fc.string({maxLength: 64}), line: fc.integer({min: 1, max: 10000}), expression: fc.string({minLength: 1, maxLength: 64})}), {maxLength: 10}), {nil: undefined}),
}).map((snap: Snapshot) => {
  // Ensure all edge endpoints exist in nodes
  const nodeIds = new Set(snap.nodes.map((n: GraphNode) => n.id));
  const validEdges = snap.edges.filter((e: GraphEdge) => nodeIds.has(e.source) && nodeIds.has(e.target));
  // Ensure unresolved items have valid line numbers and non-empty expressions
  const validUnresolved = (snap.unresolved || []).filter((u: {path: string; line: number; expression: string}) => u.line >= 1 && u.expression.length > 0);
  return {...snap, edges: validEdges, unresolved: validUnresolved.length > 0 ? validUnresolved : undefined};
});

const filtersArb: fc.Arbitrary<Filters> = fc.record({
  query: fc.string({maxLength: 100}),
  kind: fc.string({maxLength: 20}),
  relation: fc.string({maxLength: 20}),
  evidence: fc.string({maxLength: 20}),
  directory: fc.string({maxLength: 64}),
  view: fc.constantFrom<'modules' | 'files' | 'symbols' | 'all'>('modules', 'files', 'symbols', 'all'),
  focus: fc.option(nodeIdArb, {nil: null}),
  hops: fc.nat({max: 10}),
  direction: fc.constantFrom<'both' | 'out' | 'in'>('both', 'out', 'in'),
});

// ---------------------------------------------------------------------------
// parseSnapshot invariants
// ---------------------------------------------------------------------------

test('parseSnapshot: valid snapshots round-trip with defaults', () => {
  fc.assert(
    fc.property(snapshotArb, (snap: Snapshot) => {
      const parsed = parseSnapshot(snap);
      assert.equal(parsed.version, snap.version);
      assert.equal(parsed.name, snap.name);
      assert.equal(parsed.nodes.length, snap.nodes.length);
      assert.equal(parsed.edges.length, snap.edges.length);
      assert.deepEqual(parsed.warnings, snap.warnings);
      assert.equal(parsed.truncated, snap.truncated);
    }),
    {numRuns: 200}
  );
});

test('parseSnapshot: rejects invalid version', () => {
  fc.assert(
    fc.property(
      snapshotArb,
      fc.integer({max: 0}),
      (snap: Snapshot, badVersion: number) => {
        assert.throws(() => parseSnapshot({...snap, version: badVersion}));
      }
    ),
    {numRuns: 100}
  );
});

test('parseSnapshot: rejects duplicate node ids', () => {
  fc.assert(
    fc.property(
      snapshotArb,
      (snap: Snapshot) => {
        if (snap.nodes.length === 0) return;
        const dup = {...snap.nodes[0]};
        assert.throws(() => parseSnapshot({...snap, nodes: [dup, ...snap.nodes]}));
      }
    ),
    {numRuns: 100}
  );
});

test('parseSnapshot: rejects edges with missing endpoints', () => {
  fc.assert(
    fc.property(
      snapshotArb,
      fc.string({minLength: 1, maxLength: 32}).map((s: string) => s.replace(/[^a-zA-Z0-9:._-]/g, '_')),
      (snap: Snapshot, missingId: string) => {
        // Ensure missingId is not already a node id
        const nodeIds = new Set(snap.nodes.map((n: GraphNode) => n.id));
        if (nodeIds.has(missingId)) return;
        const badEdge: GraphEdge = {source: missingId, target: snap.nodes[0]?.id ?? 'x', relation: 'calls', confidence: 'parsed'};
        assert.throws(() => parseSnapshot({...snap, edges: [...snap.edges, badEdge]}));
      }
    ),
    {numRuns: 100}
  );
});

test('parseSnapshot: rejects invalid confidence values', () => {
  fc.assert(
    fc.property(
      snapshotArb,
      fc.string({maxLength: 20}),
      (snap: Snapshot, badConfidence: string) => {
        if (snap.nodes.length === 0) return;
        const badNode = {...snap.nodes[0], confidence: badConfidence as Evidence};
        assert.throws(() => parseSnapshot({...snap, nodes: [badNode, ...snap.nodes.slice(1)]}));
      }
    ),
    {numRuns: 100}
  );
});

// ---------------------------------------------------------------------------
// Graph structure invariants
// ---------------------------------------------------------------------------

test('parseSnapshot: node ids are unique after parsing', () => {
  fc.assert(
    fc.property(snapshotArb, (snap: Snapshot) => {
      const parsed = parseSnapshot(snap);
      const ids = parsed.nodes.map((n: GraphNode) => n.id);
      assert.equal(ids.length, new Set(ids).size);
    }),
    {numRuns: 200}
  );
});

test('parseSnapshot: all edge endpoints exist in nodes', () => {
  fc.assert(
    fc.property(snapshotArb, (snap: Snapshot) => {
      const parsed = parseSnapshot(snap);
      const nodeIds = new Set(parsed.nodes.map((n: GraphNode) => n.id));
      for (const edge of parsed.edges) {
        assert.ok(nodeIds.has(edge.source), `edge source ${edge.source} not in nodes`);
        assert.ok(nodeIds.has(edge.target), `edge target ${edge.target} not in nodes`);
      }
    }),
    {numRuns: 200}
  );
});

// ---------------------------------------------------------------------------
// neighborhood invariants
// ---------------------------------------------------------------------------

test('neighborhood: start node is always included', () => {
  fc.assert(
    fc.property(
      snapshotArb,
      fc.nat({max: 5}),
      fc.constantFrom<'both' | 'out' | 'in'>('both', 'out', 'in'),
      (snap: Snapshot, hops: number, direction: 'both' | 'out' | 'in') => {
        if (snap.nodes.length === 0) return;
        const start = snap.nodes[0].id;
        const result = neighborhood(snap, start, hops, direction);
        assert.ok(result.has(start));
      }
    ),
    {numRuns: 200}
  );
});

test('neighborhood: result is subset of node ids', () => {
  fc.assert(
    fc.property(
      snapshotArb,
      fc.nat({max: 5}),
      fc.constantFrom<'both' | 'out' | 'in'>('both', 'out', 'in'),
      (snap: Snapshot, hops: number, direction: 'both' | 'out' | 'in') => {
        if (snap.nodes.length === 0) return;
        const start = snap.nodes[0].id;
        const result = neighborhood(snap, start, hops, direction);
        const nodeIds = new Set(snap.nodes.map((n: GraphNode) => n.id));
        for (const id of result) {
          assert.ok(nodeIds.has(id));
        }
      }
    ),
    {numRuns: 200}
  );
});

test('neighborhood: unknown start returns empty set', () => {
  fc.assert(
    fc.property(
      snapshotArb,
      fc.nat({max: 5}),
      (snap: Snapshot, hops: number) => {
        const result = neighborhood(snap, '__nonexistent__', hops);
        assert.equal(result.size, 0);
      }
    ),
    {numRuns: 100}
  );
});

test('neighborhood: zero hops returns only start node', () => {
  fc.assert(
    fc.property(snapshotArb, (snap: Snapshot) => {
      if (snap.nodes.length === 0) return;
      const start = snap.nodes[0].id;
      const result = neighborhood(snap, start, 0);
      assert.equal(result.size, 1);
      assert.ok(result.has(start));
    }),
    {numRuns: 100}
  );
});

// ---------------------------------------------------------------------------
// shortestPath invariants
// ---------------------------------------------------------------------------

test('shortestPath: returns empty array for unknown nodes', () => {
  fc.assert(
    fc.property(snapshotArb, (snap: Snapshot) => {
      const result = shortestPath(snap, '__missing_a__', '__missing_b__');
      assert.deepEqual(result, []);
    }),
    {numRuns: 100}
  );
});

test('shortestPath: path starts at start and ends at target', () => {
  fc.assert(
    fc.property(snapshotArb, (snap: Snapshot) => {
      if (snap.nodes.length < 2) return;
      const start = snap.nodes[0].id;
      const target = snap.nodes[1].id;
      const path = shortestPath(snap, start, target);
      if (path.length > 0) {
        assert.equal(path[0], start);
        assert.equal(path[path.length - 1], target);
      }
    }),
    {numRuns: 200}
  );
});

test('shortestPath: path nodes exist in graph', () => {
  fc.assert(
    fc.property(snapshotArb, (snap: Snapshot) => {
      if (snap.nodes.length < 2) return;
      const start = snap.nodes[0].id;
      const target = snap.nodes[1].id;
      const path = shortestPath(snap, start, target);
      const nodeIds = new Set(snap.nodes.map((n: GraphNode) => n.id));
      for (const id of path) {
        assert.ok(nodeIds.has(id));
      }
    }),
    {numRuns: 200}
  );
});

test('shortestPath: consecutive nodes are connected by edges', () => {
  fc.assert(
    fc.property(snapshotArb, (snap: Snapshot) => {
      if (snap.nodes.length < 2) return;
      const start = snap.nodes[0].id;
      const target = snap.nodes[1].id;
      const path = shortestPath(snap, start, target);
      if (path.length < 2) return;
      const edgeSet = new Set(snap.edges.map((e: GraphEdge) => `${e.source}->${e.target}`));
      for (let i = 0; i < path.length - 1; i++) {
        assert.ok(edgeSet.has(`${path[i]}->${path[i+1]}`), `no edge ${path[i]}->${path[i+1]}`);
      }
    }),
    {numRuns: 200}
  );
});

// ---------------------------------------------------------------------------
// filterGraph invariants
// ---------------------------------------------------------------------------

test('filterGraph: result nodes are subset of input nodes', () => {
  fc.assert(
    fc.property(snapshotArb, filtersArb, (snap: Snapshot, filters: Filters) => {
      const result = filterGraph(snap, filters);
      const inputIds = new Set(snap.nodes.map((n: GraphNode) => n.id));
      for (const node of result.nodes) {
        assert.ok(inputIds.has(node.id));
      }
    }),
    {numRuns: 200}
  );
});

test('filterGraph: result edges have endpoints in result nodes', () => {
  fc.assert(
    fc.property(snapshotArb, filtersArb, (snap: Snapshot, filters: Filters) => {
      const result = filterGraph(snap, filters);
      const nodeIds = new Set(result.nodes.map((n: GraphNode) => n.id));
      for (const edge of result.edges) {
        assert.ok(nodeIds.has(edge.source));
        assert.ok(nodeIds.has(edge.target));
      }
    }),
    {numRuns: 200}
  );
});

test('filterGraph: node count does not exceed visible limit', () => {
  fc.assert(
    fc.property(snapshotArb, filtersArb, (snap: Snapshot, filters: Filters) => {
      const result = filterGraph(snap, filters);
      assert.ok(result.nodes.length <= 1800);
    }),
    {numRuns: 200}
  );
});

test('filterGraph: edge count does not exceed visible edge limit', () => {
  fc.assert(
    fc.property(snapshotArb, filtersArb, (snap: Snapshot, filters: Filters) => {
      const result = filterGraph(snap, filters);
      assert.ok(result.edges.length <= 12000);
    }),
    {numRuns: 200}
  );
});

test('filterGraph: matched count is >= returned node count', () => {
  fc.assert(
    fc.property(snapshotArb, filtersArb, (snap: Snapshot, filters: Filters) => {
      const result = filterGraph(snap, filters);
      assert.ok(result.matching >= result.nodes.length);
    }),
    {numRuns: 200}
  );
});

test('filterGraph: capped flag is true when nodes were truncated', () => {
  fc.assert(
    fc.property(snapshotArb, filtersArb, (snap: Snapshot, filters: Filters) => {
      const result = filterGraph(snap, filters);
      if (result.matching > result.nodes.length) {
        assert.equal(result.capped, true);
      }
    }),
    {numRuns: 200}
  );
});

// ---------------------------------------------------------------------------
// semanticEdges invariants
// ---------------------------------------------------------------------------

test('semanticEdges: excludes contains and defines relations', () => {
  fc.assert(
    fc.property(
      snapshotArb,
      fc.string({maxLength: 20}),
      (snap: Snapshot, evidence: string) => {
        const result = semanticEdges(snap, evidence);
        for (const edge of result) {
          assert.ok(edge.relation !== 'contains');
          assert.ok(edge.relation !== 'defines');
        }
      }
    ),
    {numRuns: 200}
  );
});

test('semanticEdges: result is subset of input edges', () => {
  fc.assert(
    fc.property(
      snapshotArb,
      fc.string({maxLength: 20}),
      (snap: Snapshot, evidence: string) => {
        const result = semanticEdges(snap, evidence);
        const edgeSet = new Set(snap.edges.map((e: GraphEdge) => `${e.source}->${e.target}->${e.relation}`));
        for (const edge of result) {
          assert.ok(edgeSet.has(`${edge.source}->${edge.target}->${edge.relation}`));
        }
      }
    ),
    {numRuns: 200}
  );
});

// ---------------------------------------------------------------------------
// indexGraph invariants
// ---------------------------------------------------------------------------

test('indexGraph: all nodes are indexed', () => {
  fc.assert(
    fc.property(snapshotArb, (snap: Snapshot) => {
      const index = indexGraph(snap);
      for (const node of snap.nodes) {
        assert.ok(index.nodes.has(node.id));
      }
    }),
    {numRuns: 200}
  );
});

test('indexGraph: outgoing edges match edge list', () => {
  fc.assert(
    fc.property(snapshotArb, (snap: Snapshot) => {
      const index = indexGraph(snap);
      for (const edge of snap.edges) {
        const out = index.out.get(edge.source) || [];
        assert.ok(out.some((e: GraphEdge) => e.target === edge.target && e.relation === edge.relation));
      }
    }),
    {numRuns: 200}
  );
});

test('indexGraph: incoming edges match edge list', () => {
  fc.assert(
    fc.property(snapshotArb, (snap: Snapshot) => {
      const index = indexGraph(snap);
      for (const edge of snap.edges) {
        const incoming = index.incoming.get(edge.target) || [];
        assert.ok(incoming.some((e: GraphEdge) => e.source === edge.source && e.relation === edge.relation));
      }
    }),
    {numRuns: 200}
  );
});

// ---------------------------------------------------------------------------
// Determinism
// ---------------------------------------------------------------------------

test('parseSnapshot: deterministic output', () => {
  fc.assert(
    fc.property(snapshotArb, (snap: Snapshot) => {
      const r1 = parseSnapshot(snap);
      const r2 = parseSnapshot(snap);
      assert.deepEqual(r1, r2);
    }),
    {numRuns: 100}
  );
});

test('filterGraph: deterministic output', () => {
  fc.assert(
    fc.property(snapshotArb, filtersArb, (snap: Snapshot, filters: Filters) => {
      const r1 = filterGraph(snap, filters);
      const r2 = filterGraph(snap, filters);
      assert.deepEqual(r1.nodes.map((n: GraphNode) => n.id), r2.nodes.map((n: GraphNode) => n.id));
      assert.deepEqual(r1.edges, r2.edges);
    }),
    {numRuns: 100}
  );
});

test('neighborhood: deterministic output', () => {
  fc.assert(
    fc.property(
      snapshotArb,
      fc.nat({max: 5}),
      fc.constantFrom<'both' | 'out' | 'in'>('both', 'out', 'in'),
      (snap: Snapshot, hops: number, direction: 'both' | 'out' | 'in') => {
        if (snap.nodes.length === 0) return;
        const start = snap.nodes[0].id;
        const r1 = neighborhood(snap, start, hops, direction);
        const r2 = neighborhood(snap, start, hops, direction);
        assert.deepEqual([...r1].sort(), [...r2].sort());
      }
    ),
    {numRuns: 100}
  );
});
