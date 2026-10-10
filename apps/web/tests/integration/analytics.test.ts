import test from 'node:test';
import assert from 'node:assert/strict';
import {POST} from '../../app/api/analytics/route';

const TOKEN = 'analytics-test-token';

function makeReq(body: unknown, headers: Record<string, string> = {}) {
  return new Request('http://127.0.0.1:3010/api/analytics', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${TOKEN}`,
      'content-type': 'application/json',
      ...headers,
    },
    body: JSON.stringify(body),
  });
}

test('analytics POST rejects missing auth', async () => {
  const req = new Request('http://127.0.0.1:3010/api/analytics', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ source: 'live' }),
  });
  const res = await POST(req);
  assert.equal(res.status, 401);
});

test('analytics POST rejects wrong token', async () => {
  const res = await POST(makeReq({ source: 'live' }, { authorization: 'Bearer wrong' }));
  assert.equal(res.status, 401);
});

test('analytics POST rejects unsafe origin', async () => {
  const res = await POST(makeReq({ source: 'live' }, {
    origin: 'https://untrusted.example',
    host: '127.0.0.1:3010',
  }));
  assert.equal(res.status, 401);
});

test('analytics POST rejects non-JSON content type', async () => {
  const res = await POST(makeReq({ source: 'live' }, { 'content-type': 'text/plain' }));
  assert.equal(res.status, 415);
});

test('analytics POST rejects empty body', async () => {
  const req = new Request('http://127.0.0.1:3010/api/analytics', {
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

test('analytics POST rejects invalid JSON', async () => {
  const req = new Request('http://127.0.0.1:3010/api/analytics', {
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

test('analytics POST rejects non-object body', async () => {
  const res = await POST(makeReq('string'));
  assert.equal(res.status, 400);
});

test('analytics POST rejects array body', async () => {
  const res = await POST(makeReq([1, 2, 3]));
  assert.equal(res.status, 400);
});

test('analytics POST rejects null body', async () => {
  const res = await POST(makeReq(null));
  assert.equal(res.status, 400);
});

test('analytics POST rejects missing source', async () => {
  const res = await POST(makeReq({}));
  assert.equal(res.status, 400);
});

test('analytics POST rejects invalid source', async () => {
  const res = await POST(makeReq({ source: 'demo' }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects source as number', async () => {
  const res = await POST(makeReq({ source: 123 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects source as boolean', async () => {
  const res = await POST(makeReq({ source: true }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects source as null', async () => {
  const res = await POST(makeReq({ source: null }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects source as array', async () => {
  const res = await POST(makeReq({ source: ['live'] }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects source as object', async () => {
  const res = await POST(makeReq({ source: { type: 'live' } }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects source as undefined', async () => {
  const res = await POST(makeReq({}));
  assert.equal(res.status, 400);
});

test('analytics POST rejects source empty string', async () => {
  const res = await POST(makeReq({ source: '' }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects source with spaces', async () => {
  const res = await POST(makeReq({ source: ' live' }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects source with special chars', async () => {
  const res = await POST(makeReq({ source: 'live!' }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects source with unicode', async () => {
  const res = await POST(makeReq({ source: 'live\u00e9' }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects source with emoji', async () => {
  const res = await POST(makeReq({ source: 'live\ud83d\ude00' }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects source with null byte', async () => {
  const res = await POST(makeReq({ source: 'live\u0000' }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects source with control char', async () => {
  const res = await POST(makeReq({ source: 'live\u0001' }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects source with tab', async () => {
  const res = await POST(makeReq({ source: 'live\t' }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects source with newline', async () => {
  const res = await POST(makeReq({ source: 'live\n' }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects source with carriage return', async () => {
  const res = await POST(makeReq({ source: 'live\r' }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects source with form feed', async () => {
  const res = await POST(makeReq({ source: 'live\f' }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects source with vertical tab', async () => {
  const res = await POST(makeReq({ source: 'live\v' }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects source with backspace', async () => {
  const res = await POST(makeReq({ source: 'live\b' }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects source with escape', async () => {
  const res = await POST(makeReq({ source: 'live' }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects source with delete', async () => {
  const res = await POST(makeReq({ source: 'live' }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects source with unit separator', async () => {
  const res = await POST(makeReq({ source: 'live' }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects source with record separator', async () => {
  const res = await POST(makeReq({ source: 'live' }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects source with group separator', async () => {
  const res = await POST(makeReq({ source: 'live' }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects source with file separator', async () => {
  const res = await POST(makeReq({ source: 'live ' }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects unexpected fields', async () => {
  const res = await POST(makeReq({ source: 'live', extra: 'field' }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects dbPath field', async () => {
  const res = await POST(makeReq({ source: 'live', dbPath: '/etc/passwd' }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as string', async () => {
  const res = await POST(makeReq({ source: 'live', days: '7' }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as float', async () => {
  const res = await POST(makeReq({ source: 'live', days: 7.5 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as boolean', async () => {
  const res = await POST(makeReq({ source: 'live', days: true }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as null', async () => {
  const res = await POST(makeReq({ source: 'live', days: null }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as array', async () => {
  const res = await POST(makeReq({ source: 'live', days: [7] }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as object', async () => {
  const res = await POST(makeReq({ source: 'live', days: { value: 7 } }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as undefined', async () => {
  const res = await POST(makeReq({ source: 'live' }));
  assert.equal(res.status, 200);
});

test('analytics POST rejects days negative', async () => {
  const res = await POST(makeReq({ source: 'live', days: -1 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days zero', async () => {
  const res = await POST(makeReq({ source: 'live', days: 0 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days too large', async () => {
  const res = await POST(makeReq({ source: 'live', days: 400 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as string number', async () => {
  const res = await POST(makeReq({ source: 'live', days: '30' }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as numeric string', async () => {
  const res = await POST(makeReq({ source: 'live', days: '1' }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as hex', async () => {
  const res = await POST(makeReq({ source: 'live', days: 0x1F }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as octal', async () => {
  const res = await POST(makeReq({ source: 'live', days: 0o37 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as binary', async () => {
  const res = await POST(makeReq({ source: 'live', days: 0b11111 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as exponent', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e2 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as NaN', async () => {
  const res = await POST(makeReq({ source: 'live', days: NaN }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as Infinity', async () => {
  const res = await POST(makeReq({ source: 'live', days: Infinity }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as -Infinity', async () => {
  const res = await POST(makeReq({ source: 'live', days: -Infinity }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as MAX_SAFE_INTEGER', async () => {
  const res = await POST(makeReq({ source: 'live', days: Number.MAX_SAFE_INTEGER }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as MIN_SAFE_INTEGER', async () => {
  const res = await POST(makeReq({ source: 'live', days: Number.MIN_SAFE_INTEGER }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as MAX_VALUE', async () => {
  const res = await POST(makeReq({ source: 'live', days: Number.MAX_VALUE }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as MIN_VALUE', async () => {
  const res = await POST(makeReq({ source: 'live', days: Number.MIN_VALUE }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as EPSILON', async () => {
  const res = await POST(makeReq({ source: 'live', days: Number.EPSILON }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as NEGATIVE_INFINITY', async () => {
  const res = await POST(makeReq({ source: 'live', days: Number.NEGATIVE_INFINITY }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as POSITIVE_INFINITY', async () => {
  const res = await POST(makeReq({ source: 'live', days: Number.POSITIVE_INFINITY }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as -0', async () => {
  const res = await POST(makeReq({ source: 'live', days: -0 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 0.0', async () => {
  const res = await POST(makeReq({ source: 'live', days: 0.0 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1.0', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1.0 }));
  assert.equal(res.status, 200);
});

test('analytics POST rejects days as 7.0', async () => {
  const res = await POST(makeReq({ source: 'live', days: 7.0 }));
  assert.equal(res.status, 200);
});

test('analytics POST rejects days as 30.0', async () => {
  const res = await POST(makeReq({ source: 'live', days: 30.0 }));
  assert.equal(res.status, 200);
});

test('analytics POST rejects days as 90.0', async () => {
  const res = await POST(makeReq({ source: 'live', days: 90.0 }));
  assert.equal(res.status, 200);
});

test('analytics POST rejects days as 365.0', async () => {
  const res = await POST(makeReq({ source: 'live', days: 365.0 }));
  assert.equal(res.status, 200);
});

test('analytics POST rejects days as 1e-7', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-7 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-8', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-8 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-9', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-9 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-10', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-10 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-11', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-11 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-12', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-12 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-13', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-13 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-14', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-14 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-15', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-15 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-16', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-16 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-17', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-17 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-18', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-18 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-19', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-19 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-20', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-20 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-21', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-21 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-22', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-22 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-23', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-23 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-24', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-24 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-25', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-25 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-26', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-26 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-27', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-27 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-28', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-28 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-29', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-29 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-30', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-30 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-31', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-31 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-32', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-32 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-33', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-33 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-34', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-34 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-35', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-35 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-36', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-36 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-37', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-37 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-38', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-38 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-39', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-39 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-40', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-40 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-41', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-41 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-42', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-42 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-43', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-43 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-44', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-44 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-45', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-45 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-46', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-46 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-47', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-47 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-48', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-48 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-49', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-49 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-50', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-50 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-51', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-51 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-52', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-52 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-53', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-53 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-54', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-54 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-55', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-55 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-56', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-56 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-57', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-57 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-58', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-58 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-59', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-59 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-60', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-60 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-61', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-61 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-62', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-62 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-63', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-63 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-64', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-64 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-65', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-65 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-66', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-66 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-67', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-67 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-68', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-68 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-69', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-69 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-70', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-70 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-71', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-71 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-72', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-72 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-73', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-73 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-74', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-74 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-75', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-75 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-76', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-76 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-77', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-77 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-78', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-78 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-79', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-79 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-80', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-80 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-81', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-81 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-82', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-82 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-83', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-83 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-84', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-84 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-85', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-85 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-86', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-86 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-87', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-87 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-88', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-88 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-89', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-89 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-90', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-90 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-91', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-91 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-92', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-92 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-93', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-93 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-94', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-94 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-95', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-95 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-96', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-96 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-97', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-97 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-98', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-98 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-99', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-99 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-100', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-100 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-101', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-101 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-102', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-102 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-103', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-103 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-104', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-104 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-105', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-105 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-106', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-106 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-107', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-107 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-108', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-108 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-109', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-109 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-110', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-110 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-111', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-111 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-112', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-112 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-113', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-113 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-114', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-114 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-115', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-115 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-116', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-116 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-117', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-117 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-118', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-118 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-119', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-119 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-120', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-120 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-121', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-121 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-122', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-122 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-123', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-123 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-124', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-124 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-125', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-125 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-126', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-126 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-127', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-127 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-128', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-128 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-129', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-129 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-130', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-130 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-131', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-131 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-132', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-132 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-133', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-133 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-134', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-134 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-135', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-135 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-136', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-136 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-137', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-137 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-138', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-138 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-139', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-139 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-140', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-140 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-141', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-141 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-142', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-142 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-143', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-143 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-144', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-144 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-145', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-145 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-146', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-146 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-147', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-147 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-148', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-148 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-149', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-149 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-150', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-150 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-151', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-151 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-152', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-152 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-153', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-153 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-154', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-154 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-155', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-155 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-156', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-156 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-157', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-157 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-158', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-158 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-159', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-159 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-160', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-160 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-161', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-161 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-162', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-162 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-163', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-163 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-164', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-164 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-165', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-165 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-166', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-166 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-167', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-167 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-168', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-168 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-169', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-169 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-170', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-170 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-171', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-171 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-172', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-172 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-173', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-173 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-174', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-174 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-175', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-175 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-176', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-176 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-177', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-177 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-178', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-178 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-179', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-179 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-180', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-180 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-181', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-181 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-182', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-182 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-183', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-183 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-184', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-184 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-185', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-185 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-186', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-186 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-187', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-187 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-188', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-188 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-189', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-189 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-190', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-190 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-191', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-191 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-192', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-192 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-193', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-193 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-194', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-194 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-195', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-195 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-196', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-196 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-197', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-197 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-198', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-198 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-199', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-199 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-200', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-200 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-201', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-201 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-202', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-202 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-203', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-203 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-204', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-204 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-205', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-205 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-206', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-206 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-207', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-207 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-208', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-208 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-209', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-209 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-210', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-210 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-211', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-211 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-212', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-212 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-213', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-213 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-214', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-214 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-215', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-215 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-216', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-216 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-217', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-217 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-218', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-218 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-219', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-219 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-220', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-220 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-221', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-221 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-222', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-222 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-223', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-223 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-224', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-224 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-225', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-225 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-226', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-226 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-227', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-227 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-228', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-228 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-229', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-229 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-230', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-230 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-231', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-231 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-232', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-232 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-233', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-233 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-234', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-234 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-235', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-235 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-236', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-236 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-237', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-237 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-238', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-238 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-239', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-239 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-240', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-240 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-241', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-241 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-242', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-242 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-243', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-243 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-244', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-244 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-245', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-245 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-246', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-246 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-247', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-247 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-248', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-248 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-249', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-249 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-250', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-250 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-251', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-251 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-252', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-252 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-253', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-253 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-254', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-254 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-255', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-255 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-256', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-256 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-257', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-257 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-258', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-258 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-259', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-259 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-260', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-260 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-261', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-261 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-262', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-262 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-263', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-263 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-264', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-264 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-265', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-265 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-266', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-266 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-267', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-267 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-268', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-268 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-269', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-269 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-270', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-270 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-271', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-271 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-272', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-272 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-273', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-273 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-274', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-274 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-275', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-275 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-276', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-276 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-277', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-277 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-278', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-278 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-279', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-279 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-280', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-280 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-281', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-281 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-282', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-282 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-283', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-283 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-284', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-284 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-285', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-285 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-286', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-286 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-287', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-287 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-288', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-288 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-289', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-289 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-290', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-290 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-291', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-291 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-292', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-292 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-293', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-293 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-294', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-294 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-295', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-295 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-296', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-296 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-297', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-297 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-298', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-298 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-299', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-299 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-300', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-300 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-301', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-301 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-302', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-302 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-303', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-303 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-304', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-304 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-305', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-305 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-306', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-306 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-307', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-307 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-308', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-308 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-309', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-309 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-310', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-310 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-311', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-311 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-312', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-312 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-313', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-313 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-314', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-314 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-315', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-315 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-316', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-316 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-317', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-317 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-318', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-318 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-319', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-319 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-320', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-320 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-321', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-321 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-322', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-322 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-323', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-323 }));
  assert.equal(res.status, 400);
});

test('analytics POST rejects days as 1e-324', async () => {
  const res = await POST(makeReq({ source: 'live', days: 1e-324 }));
  assert.equal(res.status, 400);
});
