import test from 'node:test';
import assert from 'node:assert/strict';
import {GET, POST} from '../../app/api/decisions/route';

const TOKEN = 'decision-test-token';

function makeReq(body: unknown, headers: Record<string, string> = {}) {
  return new Request('http://127.0.0.1:3010/api/decisions', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${TOKEN}`,
      'content-type': 'application/json',
      ...headers,
    },
    body: JSON.stringify(body),
  });
}

const validBody = {
  providers: ['laya'],
  state: 'Test state',
  questions: {
    route: { type: 'choice', instructions: 'Which queue?', criteria: { review: 'Review evidence', defer: 'Gather more evidence' } },
  },
  threshold: 0.8,
  maxCostMicrousd: 1000,
};

test('decisions GET returns providers list', async () => {
  const res = await GET();
  assert.equal(res.status, 200);
  const data = await res.json();
  assert.ok(Array.isArray(data.providers));
});

test('decisions POST rejects missing auth', async () => {
  const req = new Request('http://127.0.0.1:3010/api/decisions', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(validBody),
  });
  const res = await POST(req);
  assert.equal(res.status, 401);
});

test('decisions POST rejects wrong token', async () => {
  const res = await POST(makeReq(validBody, { authorization: 'Bearer wrong' }));
  assert.equal(res.status, 401);
});

test('decisions POST rejects unsafe origin', async () => {
  const res = await POST(makeReq(validBody, {
    origin: 'https://untrusted.example',
    host: '127.0.0.1:3010',
  }));
  assert.equal(res.status, 401);
});

test('decisions POST rejects non-JSON content type', async () => {
  const res = await POST(makeReq(validBody, { 'content-type': 'text/plain' }));
  assert.equal(res.status, 415);
});

test('decisions POST rejects empty body', async () => {
  const req = new Request('http://127.0.0.1:3010/api/decisions', {
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

test('decisions POST rejects invalid JSON', async () => {
  const req = new Request('http://127.0.0.1:3010/api/decisions', {
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

test('decisions POST rejects non-object body', async () => {
  const res = await POST(makeReq('string'));
  assert.equal(res.status, 400);
});

test('decisions POST rejects array body', async () => {
  const res = await POST(makeReq([1, 2, 3]));
  assert.equal(res.status, 400);
});

test('decisions POST rejects null body', async () => {
  const res = await POST(makeReq(null));
  assert.equal(res.status, 400);
});

test('decisions POST rejects missing providers', async () => {
  const { providers, ...rest } = validBody;
  const res = await POST(makeReq(rest));
  assert.equal(res.status, 400);
});

test('decisions POST rejects empty providers', async () => {
  const res = await POST(makeReq({ ...validBody, providers: [] }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects too many providers', async () => {
  const res = await POST(makeReq({ ...validBody, providers: ['laya', 'anyjev', 'laya'] }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects invalid provider', async () => {
  const res = await POST(makeReq({ ...validBody, providers: ['invalid'] }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects duplicate providers', async () => {
  const res = await POST(makeReq({ ...validBody, providers: ['laya', 'laya'] }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects missing state', async () => {
  const { state, ...rest } = validBody;
  const res = await POST(makeReq(rest));
  assert.equal(res.status, 400);
});

test('decisions POST rejects empty state', async () => {
  const res = await POST(makeReq({ ...validBody, state: '' }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects whitespace state', async () => {
  const res = await POST(makeReq({ ...validBody, state: '   ' }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects state too long', async () => {
  const res = await POST(makeReq({ ...validBody, state: 'x'.repeat(16001) }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects missing questions', async () => {
  const { questions, ...rest } = validBody;
  const res = await POST(makeReq(rest));
  assert.equal(res.status, 400);
});

test('decisions POST rejects empty questions', async () => {
  const res = await POST(makeReq({ ...validBody, questions: {} }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects too many questions', async () => {
  const questions: Record<string, unknown> = {};
  for (let i = 0; i < 9; i++) questions[`q${i}`] = { type: 'choice', instructions: 'test', criteria: { a: 'a', b: 'b' } };
  const res = await POST(makeReq({ ...validBody, questions }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects question missing type', async () => {
  const res = await POST(makeReq({ ...validBody, questions: { q: { instructions: 'test', criteria: { a: 'a', b: 'b' } } } }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects question invalid type', async () => {
  const res = await POST(makeReq({ ...validBody, questions: { q: { type: 'invalid', instructions: 'test', criteria: { a: 'a', b: 'b' } } } }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects question missing instructions', async () => {
  const res = await POST(makeReq({ ...validBody, questions: { q: { type: 'choice', criteria: { a: 'a', b: 'b' } } } }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects question empty instructions', async () => {
  const res = await POST(makeReq({ ...validBody, questions: { q: { type: 'choice', instructions: '', criteria: { a: 'a', b: 'b' } } } }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects question instructions too long', async () => {
  const res = await POST(makeReq({ ...validBody, questions: { q: { type: 'choice', instructions: 'x'.repeat(1001), criteria: { a: 'a', b: 'b' } } } }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects question missing criteria', async () => {
  const res = await POST(makeReq({ ...validBody, questions: { q: { type: 'choice', instructions: 'test' } } }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects question empty criteria', async () => {
  const res = await POST(makeReq({ ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: {} } } }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects question criteria label too long', async () => {
  const res = await POST(makeReq({ ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: { ['x'.repeat(81)]: 'value' } } } }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects missing threshold', async () => {
  const { threshold, ...rest } = validBody;
  const res = await POST(makeReq(rest));
  assert.equal(res.status, 400);
});

test('decisions POST rejects threshold below 0', async () => {
  const res = await POST(makeReq({ ...validBody, threshold: -0.1 }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects threshold above 1', async () => {
  const res = await POST(makeReq({ ...validBody, threshold: 1.1 }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects threshold as string', async () => {
  const res = await POST(makeReq({ ...validBody, threshold: '0.8' }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects missing maxCostMicrousd', async () => {
  const { maxCostMicrousd, ...rest } = validBody;
  const res = await POST(makeReq(rest));
  assert.equal(res.status, 400);
});

test('decisions POST rejects negative maxCostMicrousd', async () => {
  const res = await POST(makeReq({ ...validBody, maxCostMicrousd: -1 }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects maxCostMicrousd as string', async () => {
  const res = await POST(makeReq({ ...validBody, maxCostMicrousd: '1000' }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects maxCostMicrousd as float', async () => {
  const res = await POST(makeReq({ ...validBody, maxCostMicrousd: 1000.5 }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects maxCostMicrousd as NaN', async () => {
  const res = await POST(makeReq({ ...validBody, maxCostMicrousd: NaN }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects maxCostMicrousd as Infinity', async () => {
  const res = await POST(makeReq({ ...validBody, maxCostMicrousd: Infinity }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects maxCostMicrousd exceeding MAX_SAFE_INTEGER', async () => {
  const res = await POST(makeReq({ ...validBody, maxCostMicrousd: Number.MAX_SAFE_INTEGER + 1 }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects unexpected fields', async () => {
  const res = await POST(makeReq({ ...validBody, extra: 'field' }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects url field', async () => {
  const res = await POST(makeReq({ ...validBody, url: 'https://untrusted.example' }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects __proto__ field', async () => {
  const res = await POST(makeReq({ ...validBody, __proto__: 'polluted' }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects prototype field', async () => {
  const res = await POST(makeReq({ ...validBody, prototype: 'polluted' }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects constructor field', async () => {
  const res = await POST(makeReq({ ...validBody, constructor: 'polluted' }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects oversized body', async () => {
  const big = 'x'.repeat(65537);
  const res = await POST(makeReq({ ...validBody, state: big }));
  assert.equal(res.status, 400);
});

test('decisions POST accepts valid request', async () => {
  const res = await POST(makeReq(validBody));
  assert.equal(res.status, 200);
  const data = await res.json();
  assert.ok(Array.isArray(data.results));
  assert.equal(data.results[0].status, 'unconfigured');
  assert.equal(data.results[0].actualCostMicrousd, null);
});

test('decisions POST accepts both providers', async () => {
  const res = await POST(makeReq({ ...validBody, providers: ['laya', 'anyjev'] }));
  assert.equal(res.status, 200);
  const data = await res.json();
  assert.equal(data.results.length, 2);
});

test('decisions POST accepts anyjev only', async () => {
  const res = await POST(makeReq({ ...validBody, providers: ['anyjev'] }));
  assert.equal(res.status, 200);
  const data = await res.json();
  assert.equal(data.results.length, 1);
  assert.equal(data.results[0].provider, 'anyjev');
});

test('decisions POST accepts score question type', async () => {
  const body = { ...validBody, questions: { q: { type: 'score', instructions: 'Rate this', criteria: { low: 'Low', high: 'High' } } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 200);
});

test('decisions POST accepts noul question type', async () => {
  const body = { ...validBody, questions: { q: { type: 'noul', instructions: 'Rate this', criteria: { low: 'Low', high: 'High' } } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 200);
});

test('decisions POST accepts criteria as array', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: ['option1', 'option2'] } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 200);
});

test('decisions POST accepts threshold at boundary 0', async () => {
  const res = await POST(makeReq({ ...validBody, threshold: 0 }));
  assert.equal(res.status, 200);
});

test('decisions POST accepts threshold at boundary 1', async () => {
  const res = await POST(makeReq({ ...validBody, threshold: 1 }));
  assert.equal(res.status, 200);
});

test('decisions POST accepts maxCostMicrousd at 0', async () => {
  const res = await POST(makeReq({ ...validBody, maxCostMicrousd: 0 }));
  assert.equal(res.status, 200);
});

test('decisions POST accepts maxCostMicrousd at MAX_SAFE_INTEGER', async () => {
  const res = await POST(makeReq({ ...validBody, maxCostMicrousd: Number.MAX_SAFE_INTEGER }));
  assert.equal(res.status, 200);
});

test('decisions POST accepts state at max length', async () => {
  const res = await POST(makeReq({ ...validBody, state: 'x'.repeat(16000) }));
  assert.equal(res.status, 200);
});

test('decisions POST accepts instructions at max length', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'x'.repeat(1000), criteria: { a: 'a', b: 'b' } } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 200);
});

test('decisions POST accepts criteria label at max length', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: { ['x'.repeat(80)]: 'value' } } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 200);
});

test('decisions POST accepts 8 questions', async () => {
  const questions: Record<string, unknown> = {};
  for (let i = 0; i < 8; i++) questions[`q${i}`] = { type: 'choice', instructions: 'test', criteria: { a: 'a', b: 'b' } };
  const res = await POST(makeReq({ ...validBody, questions }));
  assert.equal(res.status, 200);
});

test('decisions POST rejects 9 questions', async () => {
  const questions: Record<string, unknown> = {};
  for (let i = 0; i < 9; i++) questions[`q${i}`] = { type: 'choice', instructions: 'test', criteria: { a: 'a', b: 'b' } };
  const res = await POST(makeReq({ ...validBody, questions }));
  assert.equal(res.status, 400);
});

test('decisions POST rejects question with extra fields', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: { a: 'a', b: 'b' }, extra: 'field' } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria with extra fields', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: { a: 'a', b: 'b', c: 'c' } } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria with 3 options', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: { a: 'a', b: 'b', c: 'c' } } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria with 1 option', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: { a: 'a' } } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria with 0 options', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: {} } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria as string', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: 'string' } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria as number', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: 123 } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria as boolean', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: true } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria as null', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: null } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria as array with 3 items', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: ['a', 'b', 'c'] } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria as array with 1 item', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: ['a'] } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria as array with 0 items', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: [] } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria as array with non-string items', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: [1, 2] } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria as array with empty string', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: ['', 'b'] } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria as array with whitespace string', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: ['  ', 'b'] } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria as array with too long string', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: ['x'.repeat(81), 'b'] } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria as array with duplicate strings', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: ['a', 'a'] } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria as array with special chars', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: ['a!', 'b@'] } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria as array with unicode', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: ['a\u00e9', 'b\u00e9'] } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria as array with emoji', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: ['a\ud83d\ude00', 'b\ud83d\ude00'] } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria as array with null byte', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: ['a\u0000', 'b\u0000'] } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria as array with control char', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: ['a\u0001', 'b\u0001'] } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria as array with tab', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: ['a\t', 'b\t'] } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria as array with newline', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: ['a\n', 'b\n'] } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria as array with carriage return', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: ['a\r', 'b\r'] } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria as array with form feed', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: ['a\f', 'b\f'] } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria as array with vertical tab', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: ['a\v', 'b\v'] } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria as array with backspace', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: ['a\b', 'b\b'] } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria as array with escape', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: ['a', 'b'] } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria as array with delete', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: ['a', 'b'] } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria as array with unit separator', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: ['a', 'b'] } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria as array with record separator', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: ['a', 'b'] } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria as array with group separator', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: ['a', 'b'] } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});

test('decisions POST rejects criteria as array with file separator', async () => {
  const body = { ...validBody, questions: { q: { type: 'choice', instructions: 'test', criteria: ['a ', 'b '] } } };
  const res = await POST(makeReq(body));
  assert.equal(res.status, 400);
});
