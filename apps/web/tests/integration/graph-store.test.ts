import test from 'node:test';
import assert from 'node:assert/strict';
import {GET, POST} from '../../app/api/graph-store/route';
import {getNeo4jConfig, GRAPH_STORE_MAX_BYTES, GRAPH_STORE_TIMEOUT_MS} from '../../lib/neo4j-store';

const TOKEN = 'graph-store-test-token';

function makeReq(body: unknown, headers: Record<string, string> = {}) {
  return new Request('http://127.0.0.1:3010/api/graph-store', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${TOKEN}`,
      'content-type': 'application/json',
      ...headers,
    },
    body: JSON.stringify(body),
  });
}

test('graph-store GET returns enabled flag and mode', async () => {
  const res = await GET();
  assert.equal(res.status, 200);
  const data = await res.json();
  assert.equal(typeof data.enabled, 'boolean');
  assert.equal(data.mode, 'neo4j');
});

test('graph-store POST rejects missing auth', async () => {
  const req = new Request('http://127.0.0.1:3010/api/graph-store', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ action: 'load' }),
  });
  const res = await POST(req);
  assert.equal(res.status, 401);
});

test('graph-store POST rejects wrong token', async () => {
  const res = await POST(makeReq({ action: 'load' }, { authorization: 'Bearer wrong' }));
  assert.equal(res.status, 401);
});

test('graph-store POST rejects unsafe origin', async () => {
  const res = await POST(makeReq({ action: 'load' }, {
    origin: 'https://untrusted.example',
    host: '127.0.0.1:3010',
  }));
  assert.equal(res.status, 403);
});

test('graph-store POST rejects non-JSON content type', async () => {
  const res = await POST(makeReq({ action: 'load' }, { 'content-type': 'text/plain' }));
  assert.equal(res.status, 415);
});

test('graph-store POST rejects invalid action', async () => {
  const res = await POST(makeReq({ action: 'delete' }));
  assert.equal(res.status, 400);
});

test('graph-store POST rejects missing action', async () => {
  const res = await POST(makeReq({}));
  assert.equal(res.status, 400);
});

test('graph-store POST rejects non-object body', async () => {
  const res = await POST(makeReq('string'));
  assert.equal(res.status, 400);
});

test('graph-store POST rejects array body', async () => {
  const res = await POST(makeReq([1, 2, 3]));
  assert.equal(res.status, 400);
});

test('graph-store POST rejects null body', async () => {
  const res = await POST(makeReq(null));
  assert.equal(res.status, 400);
});

test('graph-store POST rejects invalid JSON', async () => {
  const req = new Request('http://127.0.0.1:3010/api/graph-store', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${TOKEN}`,
      'content-type': 'application/json',
    },
    body: '{invalid json',
  });
  const res = await POST(req);
  assert.equal(res.status, 400);
});

test('graph-store POST rejects empty body', async () => {
  const req = new Request('http://127.0.0.1:3010/api/graph-store', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${TOKEN}`,
      'content-type': 'application/json',
    },
    body: '',
  });
  const res = await POST(req);
  assert.equal(res.status, 400);
});

test('graph-store POST rejects oversized body', async () => {
  const big = 'x'.repeat(GRAPH_STORE_MAX_BYTES + 1);
  const res = await POST(makeReq({ action: 'load', data: big }));
  assert.equal(res.status, 413);
});

test('graph-store POST load without config returns 503', async () => {
  const oldUri = process.env.NEO4J_URI;
  const oldUser = process.env.NEO4J_USERNAME;
  const oldPass = process.env.NEO4J_PASSWORD;
  const oldNs = process.env.GRAPH_STORE_NAMESPACE;
  const oldToken = process.env.GRAPH_STORE_ACCESS_TOKEN;
  delete process.env.NEO4J_URI;
  delete process.env.NEO4J_USERNAME;
  delete process.env.NEO4J_PASSWORD;
  delete process.env.GRAPH_STORE_NAMESPACE;
  process.env.GRAPH_STORE_ACCESS_TOKEN = TOKEN;
  try {
    const res = await POST(makeReq({ action: 'load' }));
    assert.equal(res.status, 503);
  } finally {
    if (oldUri !== undefined) process.env.NEO4J_URI = oldUri;
    if (oldUser !== undefined) process.env.NEO4J_USERNAME = oldUser;
    if (oldPass !== undefined) process.env.NEO4J_PASSWORD = oldPass;
    if (oldNs !== undefined) process.env.GRAPH_STORE_NAMESPACE = oldNs;
    if (oldToken === undefined) delete process.env.GRAPH_STORE_ACCESS_TOKEN;
    else process.env.GRAPH_STORE_ACCESS_TOKEN = oldToken;
  }
});

test('graph-store POST save without graph field returns 400', async () => {
  const oldUri = process.env.NEO4J_URI;
  const oldUser = process.env.NEO4J_USERNAME;
  const oldPass = process.env.NEO4J_PASSWORD;
  const oldNs = process.env.GRAPH_STORE_NAMESPACE;
  const oldToken = process.env.GRAPH_STORE_ACCESS_TOKEN;
  process.env.NEO4J_URI = 'http://localhost:7687';
  process.env.NEO4J_USERNAME = 'neo4j';
  process.env.NEO4J_PASSWORD = 'password';
  process.env.GRAPH_STORE_NAMESPACE = 'test';
  process.env.GRAPH_STORE_ACCESS_TOKEN = TOKEN;
  try {
    const res = await POST(makeReq({ action: 'save' }));
    assert.equal(res.status, 400);
  } finally {
    if (oldUri === undefined) delete process.env.NEO4J_URI; else process.env.NEO4J_URI = oldUri;
    if (oldUser === undefined) delete process.env.NEO4J_USERNAME; else process.env.NEO4J_USERNAME = oldUser;
    if (oldPass === undefined) delete process.env.NEO4J_PASSWORD; else process.env.NEO4J_PASSWORD = oldPass;
    if (oldNs === undefined) delete process.env.GRAPH_STORE_NAMESPACE; else process.env.GRAPH_STORE_NAMESPACE = oldNs;
    if (oldToken === undefined) delete process.env.GRAPH_STORE_ACCESS_TOKEN; else process.env.GRAPH_STORE_ACCESS_TOKEN = oldToken;
  }
});

test('graph-store POST save with invalid graph returns 502', async () => {
  const oldUri = process.env.NEO4J_URI;
  const oldUser = process.env.NEO4J_USERNAME;
  const oldPass = process.env.NEO4J_PASSWORD;
  const oldNs = process.env.GRAPH_STORE_NAMESPACE;
  const oldToken = process.env.GRAPH_STORE_ACCESS_TOKEN;
  process.env.NEO4J_URI = 'http://localhost:7687';
  process.env.NEO4J_USERNAME = 'neo4j';
  process.env.NEO4J_PASSWORD = 'password';
  process.env.GRAPH_STORE_NAMESPACE = 'test';
  process.env.GRAPH_STORE_ACCESS_TOKEN = TOKEN;
  try {
    const res = await POST(makeReq({ action: 'save', graph: 'not-a-graph' }));
    assert.equal(res.status, 502);
  } finally {
    if (oldUri === undefined) delete process.env.NEO4J_URI; else process.env.NEO4J_URI = oldUri;
    if (oldUser === undefined) delete process.env.NEO4J_USERNAME; else process.env.NEO4J_USERNAME = oldUser;
    if (oldPass === undefined) delete process.env.NEO4J_PASSWORD; else process.env.NEO4J_PASSWORD = oldPass;
    if (oldNs === undefined) delete process.env.GRAPH_STORE_NAMESPACE; else process.env.GRAPH_STORE_NAMESPACE = oldNs;
    if (oldToken === undefined) delete process.env.GRAPH_STORE_ACCESS_TOKEN; else process.env.GRAPH_STORE_ACCESS_TOKEN = oldToken;
  }
});

test('graph-store POST load with no saved graph returns 404', async () => {
  const oldUri = process.env.NEO4J_URI;
  const oldUser = process.env.NEO4J_USERNAME;
  const oldPass = process.env.NEO4J_PASSWORD;
  const oldNs = process.env.GRAPH_STORE_NAMESPACE;
  const oldToken = process.env.GRAPH_STORE_ACCESS_TOKEN;
  process.env.NEO4J_URI = 'http://localhost:7687';
  process.env.NEO4J_USERNAME = 'neo4j';
  process.env.NEO4J_PASSWORD = 'password';
  process.env.GRAPH_STORE_NAMESPACE = 'test';
  process.env.GRAPH_STORE_ACCESS_TOKEN = TOKEN;
  try {
    const res = await POST(makeReq({ action: 'load' }));
    assert.equal(res.status, 404);
  } finally {
    if (oldUri === undefined) delete process.env.NEO4J_URI; else process.env.NEO4J_URI = oldUri;
    if (oldUser === undefined) delete process.env.NEO4J_USERNAME; else process.env.NEO4J_USERNAME = oldUser;
    if (oldPass === undefined) delete process.env.NEO4J_PASSWORD; else process.env.NEO4J_PASSWORD = oldPass;
    if (oldNs === undefined) delete process.env.GRAPH_STORE_NAMESPACE; else process.env.GRAPH_STORE_NAMESPACE = oldNs;
    if (oldToken === undefined) delete process.env.GRAPH_STORE_ACCESS_TOKEN; else process.env.GRAPH_STORE_ACCESS_TOKEN = oldToken;
  }
});

test('graph-store POST rejects extra fields in body', async () => {
  const res = await POST(makeReq({ action: 'load', extra: 'field' }));
  assert.equal(res.status, 400);
});

test('graph-store POST rejects numeric action', async () => {
  const res = await POST(makeReq({ action: 123 }));
  assert.equal(res.status, 400);
});

test('graph-store POST rejects boolean action', async () => {
  const res = await POST(makeReq({ action: true }));
  assert.equal(res.status, 400);
});

test('graph-store POST rejects null action', async () => {
  const res = await POST(makeReq({ action: null }));
  assert.equal(res.status, 400);
});

test('graph-store POST rejects empty string action', async () => {
  const res = await POST(makeReq({ action: '' }));
  assert.equal(res.status, 400);
});

test('graph-store POST rejects action with special chars', async () => {
  const res = await POST(makeReq({ action: 'load;drop' }));
  assert.equal(res.status, 400);
});

test('graph-store POST rejects action with spaces', async () => {
  const res = await POST(makeReq({ action: ' load' }));
  assert.equal(res.status, 400);
});

test('graph-store POST rejects action with newline', async () => {
  const res = await POST(makeReq({ action: 'load\n' }));
  assert.equal(res.status, 400);
});

test('graph-store POST rejects action with unicode', async () => {
  const res = await POST(makeReq({ action: 'load\u00e9' }));
  assert.equal(res.status, 400);
});

test('graph-store POST rejects action with emoji', async () => {
  const res = await POST(makeReq({ action: 'load\ud83d\ude00' }));
  assert.equal(res.status, 400);
});

test('graph-store POST rejects action with null byte', async () => {
  const res = await POST(makeReq({ action: 'load\u0000' }));
  assert.equal(res.status, 400);
});

test('graph-store POST rejects action with control chars', async () => {
  const res = await POST(makeReq({ action: 'load\u0001' }));
  assert.equal(res.status, 400);
});

test('graph-store POST rejects action with tab', async () => {
  const res = await POST(makeReq({ action: 'load\t' }));
  assert.equal(res.status, 400);
});

test('graph-store POST rejects action with carriage return', async () => {
  const res = await POST(makeReq({ action: 'load\r' }));
  assert.equal(res.status, 400);
});

test('graph-store POST rejects action with form feed', async () => {
  const res = await POST(makeReq({ action: 'load\f' }));
  assert.equal(res.status, 400);
});

test('graph-store POST rejects action with vertical tab', async () => {
  const res = await POST(makeReq({ action: 'load\v' }));
  assert.equal(res.status, 400);
});

test('graph-store POST rejects action with backspace', async () => {
  const res = await POST(makeReq({ action: 'load\b' }));
  assert.equal(res.status, 400);
});

test('graph-store POST rejects action with escape', async () => {
  const res = await POST(makeReq({ action: 'load' }));
  assert.equal(res.status, 400);
});

test('graph-store POST rejects action with delete', async () => {
  const res = await POST(makeReq({ action: 'load' }));
  assert.equal(res.status, 400);
});

test('graph-store POST rejects action with unit separator', async () => {
  const res = await POST(makeReq({ action: 'load' }));
  assert.equal(res.status, 400);
});

test('graph-store POST rejects action with record separator', async () => {
  const res = await POST(makeReq({ action: 'load' }));
  assert.equal(res.status, 400);
});

test('graph-store POST rejects action with group separator', async () => {
  const res = await POST(makeReq({ action: 'load' }));
  assert.equal(res.status, 400);
});

test('graph-store POST rejects action with file separator', async () => {
  const res = await POST(makeReq({ action: 'load ' }));
  assert.equal(res.status, 400);
});
