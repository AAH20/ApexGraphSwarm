import test from 'node:test';
import assert from 'node:assert/strict';
import {getDecisionProviders, runDecisions, validateDecisionInput} from '../lib/decision-runtime';
import type {DecisionInput} from '../lib/decision-types';

const baseInput = {
  providers: ['laya'] as const,
  state: 'Bounded fixture context.',
  questions: {
    route: {type: 'choice' as const, instructions: 'Choose a route.', criteria: {review: 'Review evidence', defer: 'Gather evidence'}},
    quality: {type: 'score' as const, instructions: 'Score the evidence.', criteria: ['low', 'medium', 'high']},
    safe: {type: 'noul' as const, instructions: 'Is this safe?'}
  },
  threshold: 0.75,
  maxCostMicrousd: 100,
};
const env = {
  LAYA_PREDICT_URL: 'https://laya.example/v1/systemone',
  LAYA_API_KEY: 'fixture-secret',
  LAYA_COST_MICROUSD_PER_QUESTION: '5',
};
const envelope = {
  model: 'fixture-model',
  answers: {
    route: {type: 'choice', value: 'review', confidence: 0.8, distribution: {review: 0.8, defer: 0.2}},
    quality: {type: 'score', value: 1.1, confidence: 0.7, distribution: {low: 0.1, medium: 0.7, high: 0.2}},
    safe: {type: 'noul', value: 0.1, confidence: 0.9, distribution: {false: 0.9, true: 0.1}},
  },
  usage: null,
  routing: {level: 'L0'},
};
const jsonResponse = (body: unknown, status = 200) => new Response(JSON.stringify(body), {status, headers: {'content-type': 'application/json'}});

test('validates exact bounded schema and rejects prototype keys and unsafe numeric values', () => {
  assert.equal(validateDecisionInput(baseInput).state, baseInput.state);
  const cases: unknown[] = [
    {...baseInput, providers: ['laya', 'laya']},
    {...baseInput, providerUrl: 'https://attacker.example'},
    {...baseInput, maxCostMicrousd: 1.5},
    {...baseInput, maxCostMicrousd: Number.MAX_SAFE_INTEGER + 1},
    {...baseInput, threshold: Number.NaN},
    {...baseInput, state: ''},
    {...baseInput, state: 'x'.repeat(16_001)},
    {...baseInput, questions: {constructor: {type: 'noul', instructions: 'Unsafe key'}}},
    {...baseInput, questions: {route: {type: 'choice', instructions: 'bad', criteria: JSON.parse('{"__proto__":"pollution","valid":"valid"}')}}},
    {...baseInput, questions: {route: {type: 'choice', instructions: 'bad', criteria: {constructor: 'dangerous', valid: 'valid'}}}},
  ];
  for (const value of cases) assert.throws(() => validateDecisionInput(value), (error: unknown) => (error as Error).name === 'DecisionRuntimeError');
});

test('reports safe configuration without exposing endpoint or bearer secret', () => {
  const info = getDecisionProviders({...env, ANYJEV_PREDICT_URL: 'http://192.168.1.3/predict', ANYJEV_API_KEY: 'private', ANYJEV_COST_MICROUSD_PER_QUESTION: '2'});
  assert.equal(info[0].configured, true);
  assert.equal(info[0].estimatedCostPerQuestionMicrousd, 5);
  assert.equal(info[1].configured, false);
  assert.equal(JSON.stringify(info).includes('laya.example'), false);
  assert.equal(JSON.stringify(info).includes('fixture-secret'), false);
});

test('preflights combined cost before any requested provider is dispatched', async () => {
  let calls = 0;
  const input: DecisionInput = {...baseInput, providers: ['laya', 'anyjev'], maxCostMicrousd: 29};
  const twoProviderEnv = {...env, ANYJEV_PREDICT_URL: 'http://127.0.0.1:9900/predict', ANYJEV_API_KEY: 'local-secret', ANYJEV_COST_MICROUSD_PER_QUESTION: '5'};
  const results = await runDecisions(input, twoProviderEnv, async () => { calls++; return jsonResponse(envelope); });
  assert.equal(calls, 0);
  assert.deepEqual(results.map(result => result.status), ['failed', 'failed']);
  assert.ok(results.every(result => result.actualCostMicrousd === null && result.error?.includes('no provider was called')));
});

test('normalizes bridge envelope with unknown token and actual cost kept unknown', async () => {
  let requestUrl = '', requestAuthorization = '', requestBody = '';
  const results = await runDecisions(baseInput, env, async (input, init) => {
    requestUrl = String(input);
    requestAuthorization = new Headers(init?.headers).get('authorization') ?? '';
    requestBody = String(init?.body);
    return jsonResponse(envelope);
  });
  assert.equal(requestUrl, env.LAYA_PREDICT_URL);
  assert.equal(requestAuthorization, 'Bearer fixture-secret');
  assert.equal(JSON.parse(requestBody).state, baseInput.state);
  assert.equal(results[0].status, 'succeeded');
  assert.equal(results[0].estimatedCostMicrousd, 15);
  assert.equal(results[0].actualCostMicrousd, null);
  assert.equal(results[0].answers[0].reviewRequired, false);
  assert.equal(results[0].answers[2].reviewRequired, false);
  assert.ok(results[0].warnings.some(warning => warning.includes('repository-wide coverage is unverified')));
});

test('parses native Laya answer types and rejects mismatched distributions or missing questions', async () => {
  const native = {
    model: 'laya-native',
    answers: {
      route: {type: 'choice', choice: 'review', probabilities: {review: 0.8, defer: 0.2}, confidence: 0.5, answer_confidence: 0.8},
      quality: {type: 'score', score: 1.1, probabilities: {'0': 0.1, '1': 0.7, '2': 0.2}, confidence: 0.7, answer_confidence: 0.7},
      safe: {type: 'noul', noul: 0.1, confidence: 0.9, answer_confidence: 0.9},
    },
  };
  const success = await runDecisions(baseInput, env, async () => jsonResponse(native));
  assert.equal(success[0].status, 'succeeded');
  assert.deepEqual(success[0].answers[1].distribution, {low: 0.1, medium: 0.7, high: 0.2});
  const malformed = await runDecisions(baseInput, env, async () => jsonResponse({...native, answers: {...native.answers, safe: undefined}}));
  assert.equal(malformed[0].status, 'failed');
  assert.match(malformed[0].error ?? '', /did not match/);
});

test('fails closed on malformed probability mass, unsafe confidence, and untrusted remote text', async () => {
  const unsafe = {...envelope, answers: {...envelope.answers, route: {type: 'choice', value: 'invented', confidence: 4, distribution: {invented: 1}}}};
  const results = await runDecisions(baseInput, env, async () => jsonResponse(unsafe));
  assert.equal(results[0].status, 'failed');
  assert.equal(JSON.stringify(results).includes('invented'), false);
  const badMass = {...envelope, answers: {...envelope.answers, route: {type: 'choice', value: 'review', confidence: 0.8, distribution: {review: 0.4, defer: 0.2}}}};
  assert.equal((await runDecisions(baseInput, env, async () => jsonResponse(badMass)))[0].status, 'failed');
});

test('does not follow redirects and bounds response reads', async () => {
  let redirectMode = '';
  const redirect = await runDecisions(baseInput, env, async (_input, init) => {
    redirectMode = String(init?.redirect);
    return new Response('', {status: 307, headers: {location: 'https://attacker.example'}});
  });
  assert.equal(redirectMode, 'manual');
  assert.equal(redirect[0].status, 'failed');
  const large = await runDecisions(baseInput, env, async () => new Response(' '.repeat(256 * 1024 + 1)));
  assert.equal(large[0].status, 'failed');
  assert.match(large[0].error ?? '', /256 KiB/);
});

test('times out without retrying and retains cost uncertainty', async () => {
  const started = Date.now();
  const results = await runDecisions(baseInput, env, async (_input, init) => new Promise<Response>((_resolve, reject) => {
    init?.signal?.addEventListener('abort', () => reject(new Error('aborted')), {once: true});
  }));
  assert.ok(Date.now() - started < 16_000);
  assert.equal(results[0].status, 'failed');
  assert.match(results[0].error ?? '', /timed out/);
  assert.equal(results[0].actualCostMicrousd, null);
  assert.equal(results[0].estimatedCostMicrousd, 15);
});

test('unconfigured providers remain explicit and configured requests reject unsafe endpoint schemes', async () => {
  const unconfigured = await runDecisions(baseInput, {});
  assert.equal(unconfigured[0].status, 'unconfigured');
  assert.equal(unconfigured[0].estimatedCostMicrousd, null);
  const unsafe = await runDecisions(baseInput, {...env, LAYA_PREDICT_URL: 'http://public.example/predict'});
  assert.equal(unsafe[0].status, 'unconfigured');
});
