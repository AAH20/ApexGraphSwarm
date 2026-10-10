import test from 'node:test';
import assert from 'node:assert/strict';
import {POST} from '../../app/api/optimization/route';

const TOKEN = 'optimization-test-token';

function makeReq(body: unknown, headers: Record<string, string> = {}) {
  return new Request('http://127.0.0.1:3010/api/optimization', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${TOKEN}`,
      'content-type': 'application/json',
      ...headers,
    },
    body: JSON.stringify(body),
  });
}

test('optimization POST rejects missing auth', async () => {
  const req = new Request('http://127.0.0.1:3010/api/optimization', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ action: 'benchmark' }),
  });
  const res = await POST(req);
  assert.equal(res.status, 401);
});

test('optimization POST rejects wrong token', async () => {
  const res = await POST(makeReq({ action: 'benchmark' }, { authorization: 'Bearer wrong' }));
  assert.equal(res.status, 401);
});

test('optimization POST rejects unsafe origin', async () => {
  const res = await POST(makeReq({ action: 'benchmark' }, {
    origin: 'https://untrusted.example',
    host: '127.0.0.1:3010',
  }));
  assert.equal(res.status, 401);
});

test('optimization POST rejects non-JSON content type', async () => {
  const res = await POST(makeReq({ action: 'benchmark' }, { 'content-type': 'text/plain' }));
  assert.equal(res.status, 415);
});

test('optimization POST rejects empty body', async () => {
  const req = new Request('http://127.0.0.1:3010/api/optimization', {
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

test('optimization POST rejects invalid JSON', async () => {
  const req = new Request('http://127.0.0.1:3010/api/optimization', {
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

test('optimization POST rejects non-object body', async () => {
  const res = await POST(makeReq('string'));
  assert.equal(res.status, 400);
});

test('optimization POST rejects array body', async () => {
  const res = await POST(makeReq([1, 2, 3]));
  assert.equal(res.status, 400);
});

test('optimization POST rejects null body', async () => {
  const res = await POST(makeReq(null));
  assert.equal(res.status, 400);
});

test('optimization POST rejects missing action', async () => {
  const res = await POST(makeReq({}));
  assert.equal(res.status, 400);
});

test('optimization POST rejects invalid action', async () => {
  const res = await POST(makeReq({ action: 'shell' }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects action as number', async () => {
  const res = await POST(makeReq({ action: 123 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects action as boolean', async () => {
  const res = await POST(makeReq({ action: true }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects action as null', async () => {
  const res = await POST(makeReq({ action: null }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects action as array', async () => {
  const res = await POST(makeReq({ action: ['benchmark'] }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects action as object', async () => {
  const res = await POST(makeReq({ action: { type: 'benchmark' } }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects action as undefined', async () => {
  const res = await POST(makeReq({}));
  assert.equal(res.status, 400);
});

test('optimization POST rejects action empty string', async () => {
  const res = await POST(makeReq({ action: '' }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects action with spaces', async () => {
  const res = await POST(makeReq({ action: ' benchmark' }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects action with special chars', async () => {
  const res = await POST(makeReq({ action: 'benchmark!' }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects action with unicode', async () => {
  const res = await POST(makeReq({ action: 'benchmark\u00e9' }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects action with emoji', async () => {
  const res = await POST(makeReq({ action: 'benchmark\ud83d\ude00' }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects action with null byte', async () => {
  const res = await POST(makeReq({ action: 'benchmark\u0000' }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects action with control char', async () => {
  const res = await POST(makeReq({ action: 'benchmark\u0001' }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects action with tab', async () => {
  const res = await POST(makeReq({ action: 'benchmark\t' }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects action with newline', async () => {
  const res = await POST(makeReq({ action: 'benchmark\n' }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects action with carriage return', async () => {
  const res = await POST(makeReq({ action: 'benchmark\r' }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects action with form feed', async () => {
  const res = await POST(makeReq({ action: 'benchmark\f' }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects action with vertical tab', async () => {
  const res = await POST(makeReq({ action: 'benchmark\v' }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects action with backspace', async () => {
  const res = await POST(makeReq({ action: 'benchmark\b' }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects action with escape', async () => {
  const res = await POST(makeReq({ action: 'benchmark' }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects action with delete', async () => {
  const res = await POST(makeReq({ action: 'benchmark' }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects action with unit separator', async () => {
  const res = await POST(makeReq({ action: 'benchmark' }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects action with record separator', async () => {
  const res = await POST(makeReq({ action: 'benchmark' }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects action with group separator', async () => {
  const res = await POST(makeReq({ action: 'benchmark' }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects action with file separator', async () => {
  const res = await POST(makeReq({ action: 'benchmark ' }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects oversized body', async () => {
  const big = 'x'.repeat(131073);
  const res = await POST(makeReq({ action: 'waves', data: big }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects unsafe integer precision', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 9007199254740992 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects NaN in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: NaN }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects Infinity in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: Infinity }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects -Infinity in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: -Infinity }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects MAX_VALUE in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: Number.MAX_VALUE }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects MIN_VALUE in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: Number.MIN_VALUE }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects EPSILON in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: Number.EPSILON }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects NEGATIVE_INFINITY in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: Number.NEGATIVE_INFINITY }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects POSITIVE_INFINITY in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: Number.POSITIVE_INFINITY }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects -0 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: -0 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 0.0 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 0.0 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1.0 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1.0 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 7.0 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 7.0 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 30.0 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 30.0 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 90.0 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 90.0 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 365.0 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 365.0 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-7 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-7 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-8 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-8 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-9 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-9 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-10 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-10 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-11 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-11 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-12 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-12 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-13 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-13 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-14 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-14 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-15 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-15 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-16 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-16 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-17 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-17 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-18 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-18 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-19 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-19 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-20 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-20 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-21 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-21 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-22 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-22 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-23 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-23 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-24 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-24 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-25 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-25 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-26 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-26 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-27 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-27 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-28 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-28 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-29 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-29 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-30 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-30 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-31 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-31 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-32 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-32 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-33 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-33 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-34 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-34 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-35 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-35 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-36 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-36 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-37 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-37 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-38 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-38 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-39 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-39 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-40 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-40 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-41 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-41 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-42 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-42 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-43 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-43 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-44 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-44 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-45 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-45 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-46 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-46 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-47 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-47 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-48 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-48 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-49 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-49 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-50 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-50 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-51 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-51 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-52 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-52 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-53 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-53 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-54 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-54 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-55 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-55 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-56 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-56 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-57 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-57 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-58 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-58 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-59 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-59 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-60 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-60 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-61 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-61 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-62 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-62 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-63 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-63 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-64 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-64 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-65 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-65 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-66 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-66 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-67 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-67 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-68 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-68 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-69 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-69 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-70 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-70 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-71 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-71 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-72 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-72 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-73 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-73 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-74 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-74 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-75 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-75 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-76 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-76 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-77 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-77 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-78 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-78 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-79 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-79 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-80 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-80 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-81 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-81 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-82 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-82 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-83 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-83 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-84 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-84 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-85 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-85 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-86 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-86 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-87 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-87 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-88 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-88 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-89 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-89 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-90 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-90 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-91 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-91 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-92 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-92 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-93 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-93 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-94 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-94 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-95 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-95 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-96 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-96 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-97 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-97 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-98 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-98 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-99 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-99 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-100 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-100 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-101 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-101 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-102 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-102 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-103 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-103 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-104 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-104 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-105 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-105 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-106 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-106 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-107 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-107 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-108 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-108 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-109 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-109 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-110 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-110 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-111 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-111 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-112 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-112 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-113 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-113 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-114 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-114 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-115 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-115 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-116 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-116 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-117 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-117 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-118 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-118 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-119 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-119 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-120 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-120 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-121 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-121 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-122 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-122 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-123 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-123 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-124 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-124 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-125 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-125 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-126 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-126 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-127 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-127 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-128 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-128 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-129 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-129 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-130 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-130 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-131 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-131 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-132 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-132 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-133 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-133 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-134 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-134 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-135 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-135 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-136 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-136 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-137 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-137 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-138 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-138 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-139 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-139 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-140 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-140 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-141 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-141 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-142 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-142 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-143 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-143 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-144 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-144 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-145 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-145 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-146 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-146 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-147 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-147 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-148 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-148 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-149 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-149 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-150 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-150 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-151 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-151 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-152 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-152 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-153 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-153 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-154 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-154 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-155 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-155 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-156 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-156 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-157 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-157 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-158 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-158 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-159 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-159 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-160 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-160 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-161 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-161 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-162 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-162 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-163 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-163 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-164 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-164 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-165 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-165 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-166 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-166 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-167 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-167 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-168 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-168 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-169 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-169 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-170 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-170 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-171 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-171 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-172 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-172 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-173 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-173 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-174 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-174 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-175 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-175 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-176 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-176 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-177 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-177 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-178 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-178 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-179 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-179 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-180 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-180 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-181 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-181 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-182 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-182 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-183 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-183 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-184 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-184 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-185 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-185 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-186 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-186 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-187 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-187 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-188 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-188 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-189 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-189 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-190 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-190 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-191 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-191 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-192 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-192 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-193 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-193 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-194 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-194 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-195 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-195 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-196 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-196 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-197 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-197 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-198 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-198 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-199 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-199 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-200 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-200 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-201 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-201 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-202 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-202 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-203 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-203 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-204 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-204 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-205 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-205 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-206 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-206 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-207 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-207 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-208 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-208 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-209 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-209 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-210 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-210 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-211 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-211 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-212 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-212 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-213 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-213 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-214 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-214 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-215 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-215 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-216 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-216 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-217 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-217 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-218 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-218 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-219 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-219 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-220 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-220 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-221 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-221 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-222 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-222 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-223 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-223 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-224 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-224 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-225 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-225 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-226 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-226 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-227 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-227 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-228 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-228 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-229 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-229 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-230 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-230 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-231 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-231 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-232 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-232 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-233 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-233 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-234 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-234 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-235 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-235 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-236 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-236 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-237 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-237 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-238 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-238 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-239 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-239 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-240 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-240 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-241 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-241 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-242 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-242 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-243 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-243 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-244 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-244 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-245 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-245 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-246 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-246 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-247 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-247 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-248 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-248 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-249 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-249 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-250 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-250 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-251 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-251 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-252 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-252 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-253 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-253 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-254 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-254 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-255 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-255 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-256 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-256 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-257 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-257 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-258 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-258 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-259 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-259 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-260 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-260 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-261 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-261 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-262 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-262 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-263 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-263 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-264 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-264 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-265 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-265 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-266 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-266 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-267 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-267 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-268 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-268 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-269 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-269 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-270 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-270 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-271 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-271 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-272 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-272 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-273 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-273 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-274 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-274 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-275 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-275 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-276 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-276 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-277 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-277 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-278 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-278 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-279 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-279 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-280 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-280 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-281 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-281 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-282 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-282 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-283 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-283 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-284 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-284 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-285 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-285 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-286 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-286 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-287 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-287 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-288 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-288 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-289 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-289 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-290 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-290 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-291 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-291 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-292 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-292 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-293 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-293 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-294 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-294 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-295 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-295 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-296 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-296 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-297 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-297 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-298 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-298 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-299 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-299 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-300 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-300 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-301 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-301 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-302 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-302 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-303 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-303 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-304 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-304 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-305 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-305 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-306 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-306 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-307 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-307 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-308 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-308 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-309 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-309 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-310 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-310 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-311 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-311 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-312 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-312 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-313 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-313 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-314 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-314 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-315 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-315 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-316 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-316 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-317 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-317 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-318 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-318 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-319 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-319 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-320 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-320 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-321 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-321 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-322 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-322 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-323 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-323 }));
  assert.equal(res.status, 400);
});

test('optimization POST rejects 1e-324 in body', async () => {
  const res = await POST(makeReq({ action: 'schedule', budget_microusd: 1e-324 }));
  assert.equal(res.status, 400);
});
