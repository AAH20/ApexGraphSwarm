import { test } from 'node:test';
import assert from 'node:assert/strict';
import { detectViolations } from './violations.js';
import { computeTrustScore, computeAllTrustScores } from './trust.js';
import type { RunStatus, GrantSummary, WorkerSummary, PolicyViolation } from './types.js';

test('detectViolations: budget exceeded', () => {
  const run: RunStatus = {
    run: { id: 'r1', status: 'running', version: 1, budgetMicrousd: 1000, reservedMicrousd: 0, spentMicrousd: 1500, remainingMicrousd: -500, cancelRequested: false },
    agents: [],
    tasks: [],
    events: [],
  };
  const violations = detectViolations(run, [], []);
  assert.equal(violations.length, 1);
  assert.equal(violations[0].category, 'budget');
  assert.equal(violations[0].severity, 'critical');
});

test('detectViolations: no violations on healthy run', () => {
  const run: RunStatus = {
    run: { id: 'r1', status: 'running', version: 1, budgetMicrousd: 1000, reservedMicrousd: 0, spentMicrousd: 500, remainingMicrousd: 500, cancelRequested: false },
    agents: [],
    tasks: [],
    events: [],
  };
  const violations = detectViolations(run, [], []);
  assert.equal(violations.length, 0);
});

test('computeTrustScore: clean entity scores 100', () => {
  const score = computeTrustScore('w1', 'worker', [], [], []);
  assert.equal(score.score, 100);
});

test('computeTrustScore: critical violation deducts 25', () => {
  const violations: PolicyViolation[] = [
    { id: 'w1-violation-1', severity: 'critical', category: 'budget', message: 'test', timestamp: new Date().toISOString() },
  ];
  const score = computeTrustScore('w1', 'worker', violations, [], []);
  assert.equal(score.score, 75);
});

test('computeAllTrustScores: returns scores for all entities', () => {
  const workers: WorkerSummary[] = [
    { workerId: 'w1', principalId: 'p1', expiresAt: Date.now() + 10000, revokedAt: null },
    { workerId: 'w2', principalId: 'p2', expiresAt: Date.now() + 10000, revokedAt: null },
  ];
  const grants: GrantSummary[] = [
    { grantId: 'g1', principalId: 'p1', toolId: 't1', resourceId: 'r1', maxBudgetMicrousd: 1000, spentMicrousd: 500, reservedMicrousd: 0, expiresAt: Date.now() + 10000, revokedAt: null },
  ];
  const scores = computeAllTrustScores([], workers, grants);
  assert.equal(scores.length, 3);
});
