import test from 'node:test';
import assert from 'node:assert/strict';
import {POST} from '../../app/api/control/route';

const TOKEN = 'control-test-token';

function makeReq(body: unknown, headers: Record<string, string> = {}) {
  return new Request('http://127.0.0.1:3010/api/control', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${TOKEN}`,
      'content-type': 'application/json',
      ...headers,
    },
    body: JSON.stringify(body),
  });
}

test('control POST rejects missing auth', async () => {
  const req = new Request('http://127.0.0.1:3010/api/control', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ action: 'status', runId: 'test-run' }),
  });
  const res = await POST(req);
  assert.equal(res.status, 401);
});

test('control POST rejects wrong token', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'test-run' }, { authorization: 'Bearer wrong' }));
  assert.equal(res.status, 401);
});

test('control POST rejects unsafe origin', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'test-run' }, {
    origin: 'https://untrusted.example',
    host: '127.0.0.1:3010',
  }));
  assert.equal(res.status, 401);
});

test('control POST rejects non-JSON content type', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'test-run' }, { 'content-type': 'text/plain' }));
  assert.equal(res.status, 415);
});

test('control POST rejects empty body', async () => {
  const req = new Request('http://127.0.0.1:3010/api/control', {
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

test('control POST rejects invalid JSON', async () => {
  const req = new Request('http://127.0.0.1:3010/api/control', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${TOKEN}`,
      'content-type': 'application/json',
    },
    body: '{invalid',
  });
  const res = await POST(req);
  assert.equal(res.status, 400);
});

test('control POST rejects unsupported action', async () => {
  const res = await POST(makeReq({ action: 'unsupported', runId: 'test-run' }));
  assert.equal(res.status, 400);
});

test('control POST rejects unexpected fields', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'test-run', extra: 'field' }));
  assert.equal(res.status, 400);
});

test('control POST rejects non-object body', async () => {
  const res = await POST(makeReq('string'));
  assert.equal(res.status, 400);
});

test('control POST rejects array body', async () => {
  const res = await POST(makeReq([1, 2, 3]));
  assert.equal(res.status, 400);
});

test('control POST rejects null body', async () => {
  const res = await POST(makeReq(null));
  assert.equal(res.status, 400);
});

test('control POST rejects missing runId for status', async () => {
  const res = await POST(makeReq({ action: 'status' }));
  assert.equal(res.status, 400);
});

test('control POST rejects invalid runId format', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'invalid run id!' }));
  assert.equal(res.status, 400);
});

test('control POST rejects empty runId', async () => {
  const res = await POST(makeReq({ action: 'status', runId: '' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with special chars', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run@id' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with spaces', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run id' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with slash', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run/id' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with backslash', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run\\id' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with dot', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run.id' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with colon', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run:id' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with semicolon', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run;id' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with pipe', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run|id' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with ampersand', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run&id' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with percent', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run%id' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with hash', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run#id' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with question mark', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run?id' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with at sign', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run@id' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with plus', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run+id' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with equals', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run=id' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with bracket', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run[id]' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with brace', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run{id}' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with paren', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run(id)' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with angle bracket', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run<id>' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with quote', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run"id' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with apostrophe', async () => {
  const res = await POST(makeReq({ action: 'status', runId: "run'id" }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with backtick', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run`id' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with tilde', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run~id' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with caret', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run^id' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with asterisk', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run*id' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with dollar', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run$id' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with exclamation', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run!id' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with comma', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run,id' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with unicode', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run\u00e9id' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with emoji', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run\ud83d\ude00id' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with null byte', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run\u0000id' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with control char', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run\u0001id' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with tab', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run\tid' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with newline', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run\nid' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with carriage return', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run\rid' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with form feed', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run\fid' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with vertical tab', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run\vid' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with backspace', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run\bid' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with escape', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'runid' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with delete', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'runid' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with unit separator', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'runid' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with record separator', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'runid' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with group separator', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'runid' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId with file separator', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'run id' }));
  assert.equal(res.status, 400);
});

test('control POST rejects runId too long', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'a'.repeat(101) }));
  assert.equal(res.status, 400);
});

test('control POST accepts runId at max length', async () => {
  const res = await POST(makeReq({ action: 'status', runId: 'a'.repeat(100) }));
  assert.equal(res.status, 200);
});

test('control POST rejects createFixture with invalid agents', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 5, idempotencyKey: 'valid-key-123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with missing idempotencyKey', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10 }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with invalid idempotencyKey', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'short' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey too long', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'a'.repeat(101) }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey special chars', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'key@123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey spaces', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'key 123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey unicode', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'key\u00e9123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey emoji', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'key\ud83d\ude00123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey null byte', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'key\u0000123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey control char', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'key\u0001123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey tab', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'key\t123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey newline', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'key\n123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey carriage return', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'key\r123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey form feed', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'key\f123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey vertical tab', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'key\v123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey backspace', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'key\b123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey escape', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'key123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey delete', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'key123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey unit separator', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'key123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey record separator', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'key123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey group separator', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'key123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey file separator', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'key 123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with agents as string', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: '10', idempotencyKey: 'valid-key-123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with agents as float', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10.5, idempotencyKey: 'valid-key-123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with agents as boolean', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: true, idempotencyKey: 'valid-key-123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with agents as null', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: null, idempotencyKey: 'valid-key-123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with agents as array', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: [10], idempotencyKey: 'valid-key-123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with agents as object', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: { count: 10 }, idempotencyKey: 'valid-key-123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with agents as undefined', async () => {
  const res = await POST(makeReq({ action: 'createFixture', idempotencyKey: 'valid-key-123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey as number', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 12345 }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey as boolean', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: true }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey as null', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: null }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey as array', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: ['key'] }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey as object', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: { key: 'value' } }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey as undefined', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10 }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey empty string', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: '' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey whitespace', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: '   ' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey only special chars', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: '!@#$%' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey only numbers', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: '12345' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey only letters', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'abcde' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey only underscores', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: '_____' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey only hyphens', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: '-----' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123!' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey leading space', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: ' valid-key-123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey trailing space', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123 ' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey leading hyphen', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: '-valid-key-123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey trailing hyphen', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123-' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey leading underscore', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: '_valid-key-123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey trailing underscore', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123_' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey double hyphen', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid--key-123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey double underscore', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid__key-123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed case', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'Valid-Key-123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey uppercase', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'VALID-KEY-123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey lowercase', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey numeric start', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: '123-valid-key' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey numeric end', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey all numeric', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: '12345678' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey all alpha', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'abcdefghij' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey all special', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: '!@#$%^&*()' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 2', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123@' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 3', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123#' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 4', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123$' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 5', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123%' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 6', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123^' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 7', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123&' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 8', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123*' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 9', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123(' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 10', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123)' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 11', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123+' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 12', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123=' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 13', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123[' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 14', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123]' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 15', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123{' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 16', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123}' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 17', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123|' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 18', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123\\' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 19', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123/' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 20', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123?' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 21', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123<' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 22', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123>' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 23', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123,' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 24', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123.' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 25', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123:' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 26', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123;' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 27', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123"' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 28', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: "valid-key-123'" }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 29', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123`' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 30', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123~' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 31', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123^' }));
  assert.equal(res.status, 400);
});

test('control POST rejects createFixture with idempotencyKey mixed valid invalid 32', async () => {
  const res = await POST(makeReq({ action: 'createFixture', agents: 10, idempotencyKey: 'valid-key-123!' }));
  assert.equal(res.status, 400);
});
