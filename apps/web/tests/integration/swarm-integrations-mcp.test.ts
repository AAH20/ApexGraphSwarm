import test from 'node:test';
import assert from 'node:assert/strict';
import {POST as SwarmPOST} from '../../app/api/swarm/route';
import {GET as IntegrationsGET, POST as IntegrationsPOST} from '../../app/api/integrations/route';
import {GET as McpGET, POST as McpPOST} from '../../app/api/ecosystem/mcp/route';

const TOKEN = 'integration-test-token';

function makeReq(url: string, body: unknown, headers: Record<string, string> = {}) {
  return new Request(url, {
    method: 'POST',
    headers: {
      authorization: `Bearer ${TOKEN}`,
      'content-type': 'application/json',
      ...headers,
    },
    body: JSON.stringify(body),
  });
}

// Swarm endpoint tests
test('swarm POST rejects missing auth', async () => {
  const req = new Request('http://127.0.0.1:3010/api/swarm', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ graph: {}, goal: 'test' }),
  });
  const res = await SwarmPOST(req);
  assert.equal(res.status, 401);
});

test('swarm POST rejects wrong token', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: {}, goal: 'test' }, { authorization: 'Bearer wrong' }));
  assert.equal(res.status, 401);
});

test('swarm POST rejects unsafe origin', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: {}, goal: 'test' }, {
    origin: 'https://untrusted.example',
    host: '127.0.0.1:3010',
  }));
  assert.equal(res.status, 403);
});

test('swarm POST rejects non-JSON content type', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: {}, goal: 'test' }, { 'content-type': 'text/plain' }));
  assert.equal(res.status, 415);
});

test('swarm POST rejects empty body', async () => {
  const req = new Request('http://127.0.0.1:3010/api/swarm', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${TOKEN}`,
      'content-type': 'application/json',
    },
    body: '',
  });
  const res = await SwarmPOST(req);
  assert.equal(res.status, 400);
});

test('swarm POST rejects invalid JSON', async () => {
  const req = new Request('http://127.0.0.1:3010/api/swarm', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${TOKEN}`,
      'content-type': 'application/json',
    },
    body: '{invalid',
  });
  const res = await SwarmPOST(req);
  assert.equal(res.status, 400);
});

test('swarm POST rejects non-object body', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', 'string'));
  assert.equal(res.status, 400);
});

test('swarm POST rejects array body', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', [1, 2, 3]));
  assert.equal(res.status, 400);
});

test('swarm POST rejects null body', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', null));
  assert.equal(res.status, 400);
});

test('swarm POST rejects missing graph', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects missing goal', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: {} }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects empty goal', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: {}, goal: '' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects whitespace goal', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: {}, goal: '   ' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects goal too long', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: {}, goal: 'x'.repeat(2001) }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects invalid graph', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: 'invalid', goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with invalid version', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 0, name: 'test', nodes: [], edges: [] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with invalid nodes', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: 'invalid', edges: [] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with invalid edges', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: 'invalid' }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with duplicate node ids', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [{ id: 'a', name: 'a', kind: 'file', path: 'a', confidence: 'parsed' }, { id: 'a', name: 'b', kind: 'file', path: 'b', confidence: 'parsed' }], edges: [] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with dangling edge', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [{ id: 'a', name: 'a', kind: 'file', path: 'a', confidence: 'parsed' }], edges: [{ source: 'a', target: 'missing', relation: 'calls', confidence: 'parsed' }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with invalid node kind', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [{ id: 'a', name: 'a', kind: 'invalid', path: 'a', confidence: 'parsed' }], edges: [] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with invalid confidence', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [{ id: 'a', name: 'a', kind: 'file', path: 'a', confidence: 'invalid' }], edges: [] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with invalid edge relation', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [{ id: 'a', name: 'a', kind: 'file', path: 'a', confidence: 'parsed' }], edges: [{ source: 'a', target: 'a', relation: '', confidence: 'parsed' }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with invalid edge confidence', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [{ id: 'a', name: 'a', kind: 'file', path: 'a', confidence: 'parsed' }], edges: [{ source: 'a', target: 'a', relation: 'calls', confidence: 'invalid' }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with invalid warnings', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], warnings: 'invalid' }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with too many warnings', async () => {
  const warnings = Array.from({ length: 1001 }, () => 'warning');
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], warnings }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with invalid summary', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], summary: 'invalid' }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with negative unresolved', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], summary: { unresolved: -1 } }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with invalid unresolved', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], unresolved: 'invalid' }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with too many unresolved', async () => {
  const unresolved = Array.from({ length: 201 }, () => ({ path: 'test', line: 1, expression: 'test' }));
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], unresolved }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with invalid unresolved item', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], unresolved: [{ path: 'test', line: 0, expression: 'test' }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with invalid node line', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [{ id: 'a', name: 'a', kind: 'file', path: 'a', confidence: 'parsed', line: 0 }], edges: [] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with invalid node connections', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [{ id: 'a', name: 'a', kind: 'file', path: 'a', confidence: 'parsed', connections: -1 }], edges: [] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with invalid edge line', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [{ id: 'a', name: 'a', kind: 'file', path: 'a', confidence: 'parsed' }], edges: [{ source: 'a', target: 'a', relation: 'calls', confidence: 'parsed', line: 0 }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with invalid edge count', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [{ id: 'a', name: 'a', kind: 'file', path: 'a', confidence: 'parsed' }], edges: [{ source: 'a', target: 'a', relation: 'calls', confidence: 'parsed', count: 0 }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with too many nodes', async () => {
  const nodes = Array.from({ length: 25001 }, (_, i) => ({ id: `n${i}`, name: `n${i}`, kind: 'file', path: `n${i}`, confidence: 'parsed' }));
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes, edges: [] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with too many edges', async () => {
  const nodes = [{ id: 'a', name: 'a', kind: 'file', path: 'a', confidence: 'parsed' }];
  const edges = Array.from({ length: 100001 }, () => ({ source: 'a', target: 'a', relation: 'calls', confidence: 'parsed' }));
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes, edges }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with name too long', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'x'.repeat(501), nodes: [], edges: [] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with node id too long', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [{ id: 'x'.repeat(2001), name: 'a', kind: 'file', path: 'a', confidence: 'parsed' }], edges: [] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with node name too long', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [{ id: 'a', name: 'x'.repeat(2001), kind: 'file', path: 'a', confidence: 'parsed' }], edges: [] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with node path too long', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [{ id: 'a', name: 'a', kind: 'file', path: 'x'.repeat(4001), confidence: 'parsed' }], edges: [] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with node summary too long', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [{ id: 'a', name: 'a', kind: 'file', path: 'a', confidence: 'parsed', summary: 'x'.repeat(10001) }], edges: [] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with edge relation too long', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [{ id: 'a', name: 'a', kind: 'file', path: 'a', confidence: 'parsed' }], edges: [{ source: 'a', target: 'a', relation: 'x'.repeat(101), confidence: 'parsed' }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with edge source too long', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [{ id: 'a', name: 'a', kind: 'file', path: 'a', confidence: 'parsed' }], edges: [{ source: 'x'.repeat(2001), target: 'a', relation: 'calls', confidence: 'parsed' }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with edge target too long', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [{ id: 'a', name: 'a', kind: 'file', path: 'a', confidence: 'parsed' }], edges: [{ source: 'a', target: 'x'.repeat(2001), relation: 'calls', confidence: 'parsed' }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with warning too long', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], warnings: ['x'.repeat(10001)] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with unresolved path too long', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], unresolved: [{ path: 'x'.repeat(4001), line: 1, expression: 'test' }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with unresolved expression too long', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], unresolved: [{ path: 'test', line: 1, expression: 'x'.repeat(2001) }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with unresolved line too small', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], unresolved: [{ path: 'test', line: 0, expression: 'test' }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with unresolved line negative', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], unresolved: [{ path: 'test', line: -1, expression: 'test' }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with unresolved line as float', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], unresolved: [{ path: 'test', line: 1.5, expression: 'test' }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with unresolved line as string', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], unresolved: [{ path: 'test', line: '1', expression: 'test' }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with unresolved line as boolean', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], unresolved: [{ path: 'test', line: true, expression: 'test' }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with unresolved line as null', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], unresolved: [{ path: 'test', line: null, expression: 'test' }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with unresolved line as array', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], unresolved: [{ path: 'test', line: [1], expression: 'test' }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with unresolved line as object', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], unresolved: [{ path: 'test', line: { value: 1 }, expression: 'test' }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with unresolved line as undefined', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], unresolved: [{ path: 'test', expression: 'test' }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with unresolved path as number', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], unresolved: [{ path: 123, line: 1, expression: 'test' }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with unresolved path as boolean', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], unresolved: [{ path: true, line: 1, expression: 'test' }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with unresolved path as null', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], unresolved: [{ path: null, line: 1, expression: 'test' }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with unresolved path as array', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], unresolved: [{ path: ['test'], line: 1, expression: 'test' }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with unresolved path as object', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], unresolved: [{ path: { value: 'test' }, line: 1, expression: 'test' }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with unresolved path as undefined', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], unresolved: [{ line: 1, expression: 'test' }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with unresolved expression as number', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], unresolved: [{ path: 'test', line: 1, expression: 123 }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with unresolved expression as boolean', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], unresolved: [{ path: 'test', line: 1, expression: true }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with unresolved expression as null', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], unresolved: [{ path: 'test', line: 1, expression: null }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with unresolved expression as array', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], unresolved: [{ path: 'test', line: 1, expression: ['test'] }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with unresolved expression as object', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], unresolved: [{ path: 'test', line: 1, expression: { value: 'test' } }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

test('swarm POST rejects graph with unresolved expression as undefined', async () => {
  const res = await SwarmPOST(makeReq('http://127.0.0.1:3010/api/swarm', { graph: { version: 1, name: 'test', nodes: [], edges: [], unresolved: [{ path: 'test', line: 1 }] }, goal: 'test' }));
  assert.equal(res.status, 400);
});

// Integrations endpoint tests
test('integrations GET returns catalog and limits', async () => {
  const res = await IntegrationsGET();
  assert.equal(res.status, 200);
  const data = await res.json();
  assert.ok(Array.isArray(data.integrations));
  assert.ok(typeof data.limits === 'object');
});

test('integrations POST rejects missing auth', async () => {
  const req = new Request('http://127.0.0.1:3010/api/integrations', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({}),
  });
  const res = await IntegrationsPOST(req);
  assert.equal(res.status, 401);
});

test('integrations POST rejects wrong token', async () => {
  const res = await IntegrationsPOST(makeReq('http://127.0.0.1:3010/api/integrations', {}, { authorization: 'Bearer wrong' }));
  assert.equal(res.status, 401);
});

test('integrations POST rejects unsafe origin', async () => {
  const res = await IntegrationsPOST(makeReq('http://127.0.0.1:3010/api/integrations', {}, {
    origin: 'https://untrusted.example',
    host: '127.0.0.1:3010',
  }));
  assert.equal(res.status, 401);
});

test('integrations POST rejects non-JSON content type', async () => {
  const res = await IntegrationsPOST(makeReq('http://127.0.0.1:3010/api/integrations', {}, { 'content-type': 'text/plain' }));
  assert.equal(res.status, 415);
});

test('integrations POST rejects missing idempotency key', async () => {
  const res = await IntegrationsPOST(makeReq('http://127.0.0.1:3010/api/integrations', {}));
  assert.equal(res.status, 400);
});

test('integrations POST rejects empty body', async () => {
  const req = new Request('http://127.0.0.1:3010/api/integrations', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${TOKEN}`,
      'content-type': 'application/json',
      'idempotency-key': 'test-key',
    },
    body: '',
  });
  const res = await IntegrationsPOST(req);
  assert.equal(res.status, 400);
});

test('integrations POST rejects invalid JSON', async () => {
  const req = new Request('http://127.0.0.1:3010/api/integrations', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${TOKEN}`,
      'content-type': 'application/json',
      'idempotency-key': 'test-key',
    },
    body: '{invalid',
  });
  const res = await IntegrationsPOST(req);
  assert.equal(res.status, 400);
});

test('integrations POST rejects non-object body', async () => {
  const res = await IntegrationsPOST(makeReq('http://127.0.0.1:3010/api/integrations', 'string'));
  assert.equal(res.status, 400);
});

test('integrations POST rejects array body', async () => {
  const res = await IntegrationsPOST(makeReq('http://127.0.0.1:3010/api/integrations', [1, 2, 3]));
  assert.equal(res.status, 400);
});

test('integrations POST rejects null body', async () => {
  const res = await IntegrationsPOST(makeReq('http://127.0.0.1:3010/api/integrations', null));
  assert.equal(res.status, 400);
});

test('integrations POST rejects oversized body', async () => {
  const big = 'x'.repeat(2 * 1024 * 1024 + 1);
  const res = await IntegrationsPOST(makeReq('http://127.0.0.1:3010/api/integrations', { data: big }));
  assert.equal(res.status, 400);
});

// MCP endpoint tests
test('mcp GET returns catalog', async () => {
  const res = await McpGET();
  assert.equal(res.status, 200);
  const data = await res.json();
  assert.ok(typeof data === 'object');
});

test('mcp POST rejects missing auth', async () => {
  const req = new Request('http://127.0.0.1:3010/api/ecosystem/mcp', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ serverId: 'test' }),
  });
  const res = await McpPOST(req);
  assert.equal(res.status, 401);
});

test('mcp POST rejects wrong token', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test' }, { authorization: 'Bearer wrong' }));
  assert.equal(res.status, 401);
});

test('mcp POST rejects unsafe origin', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test' }, {
    origin: 'https://untrusted.example',
    host: '127.0.0.1:3010',
  }));
  assert.equal(res.status, 401);
});

test('mcp POST rejects non-JSON content type', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test' }, { 'content-type': 'text/plain' }));
  assert.equal(res.status, 415);
});

test('mcp POST rejects empty body', async () => {
  const req = new Request('http://127.0.0.1:3010/api/ecosystem/mcp', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${TOKEN}`,
      'content-type': 'application/json',
    },
    body: '',
  });
  const res = await McpPOST(req);
  assert.equal(res.status, 400);
});

test('mcp POST rejects invalid JSON', async () => {
  const req = new Request('http://127.0.0.1:3010/api/ecosystem/mcp', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${TOKEN}`,
      'content-type': 'application/json',
    },
    body: '{invalid',
  });
  const res = await McpPOST(req);
  assert.equal(res.status, 400);
});

test('mcp POST rejects non-object body', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', 'string'));
  assert.equal(res.status, 400);
});

test('mcp POST rejects array body', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', [1, 2, 3]));
  assert.equal(res.status, 400);
});

test('mcp POST rejects null body', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', null));
  assert.equal(res.status, 400);
});

test('mcp POST rejects missing serverId', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', {}));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId as number', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 123 }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId as boolean', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: true }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId as null', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: null }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId as array', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: ['test'] }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId as object', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: { id: 'test' } }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId as undefined', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', {}));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId empty string', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: '' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with spaces', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: ' test' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with special chars', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test!' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with unicode', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test\u00e9' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with emoji', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test\ud83d\ude00' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with null byte', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test\u0000' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with control char', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test\u0001' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with tab', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test\t' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with newline', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test\n' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with carriage return', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test\r' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with form feed', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test\f' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with vertical tab', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test\v' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with backspace', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test\b' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with escape', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with delete', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with unit separator', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with record separator', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with group separator', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with file separator', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test ' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects extra fields', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test', url: 'http://127.0.0.1/admin' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects oversized body', async () => {
  const big = 'x'.repeat(4097);
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: big }));
  assert.equal(res.status, 413);
});

test('mcp POST rejects serverId too long', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'a'.repeat(63) }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with only special chars', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: '!@#$%' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with only numbers', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: '12345' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with only letters', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'abcde' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with only underscores', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: '_____' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with only hyphens', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: '-----' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test!' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with leading space', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: ' test' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with trailing space', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test ' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with leading hyphen', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: '-test' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with trailing hyphen', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test-' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with leading underscore', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: '_test' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with trailing underscore', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test_' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with double hyphen', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'te--st' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with double underscore', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'te__st' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed case', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'Test' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with uppercase', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'TEST' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with lowercase', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with numeric start', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: '123test' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with numeric end', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test123' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with all numeric', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: '12345678' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with all alpha', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'abcdefghij' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with all special', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: '!@#$%^&*()' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 2', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test@' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 3', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test#' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 4', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test$' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 5', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test%' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 6', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test^' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 7', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test&' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 8', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test*' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 9', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test(' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 10', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test)' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 11', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test+' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 12', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test=' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 13', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test[' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 14', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test]' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 15', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test{' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 16', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test}' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 17', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test|' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 18', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test\\' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 19', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test/' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 20', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test?' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 21', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test<' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 22', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test>' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 23', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test,' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 24', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test.' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 25', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test:' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 26', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test;' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 27', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test"' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 28', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: "test'" }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 29', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test`' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 30', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test~' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 31', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test^' }));
  assert.equal(res.status, 400);
});

test('mcp POST rejects serverId with mixed valid invalid 32', async () => {
  const res = await McpPOST(makeReq('http://127.0.0.1:3010/api/ecosystem/mcp', { serverId: 'test!' }));
  assert.equal(res.status, 400);
});
