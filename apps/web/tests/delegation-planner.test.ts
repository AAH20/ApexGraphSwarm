import assert from 'node:assert/strict';
import test from 'node:test';
import { assessCandidate, buildDelegationPlan, createStarterCandidates, type Candidate, type PlannerRequest } from '../lib/delegation-planner';

const request = (): PlannerRequest => ({
  taskClass: 'graph-audit', goal: 'Find high-risk graph paths.', requiredCapabilities: ['graph-analysis'], privacyRequirement: 'no-training',
  inputTokens: 1000, outputTokens: 500, cacheReadTokens: 0, cacheWriteTokens: 0, agents: 2, retries: 1,
  successRatePercent: 80, plannedRunsPerMonth: 50, monthlyBudgetUsd: null, perRunBudgetUsd: null,
  allocatedSubscriptionMonthlyUsd: 0, subscriptionAllocationPercent: 100, otherFixedMonthlyUsd: 0,
  gpuRateUsdPerGpuHour: null, gpuHoursPerAttempt: null, gpuUtilizationPercent: null,
  weights: { cost: 0.6, quality: 0.3, latency: 0.1 },
});

const candidate = (overrides: Partial<Candidate> = {}): Candidate => ({
  id: 'custom/api-model-v2', name: 'Custom API route', harnessId: 'opencode', provider: 'openrouter', modelId: 'vendor/model-custom-v2',
  capabilities: ['graph-analysis'], privacy: 'no-training',
  rates: { inputPerMillionUsd: 1, outputPerMillionUsd: 2, cacheReadPerMillionUsd: 0.2, cacheWritePerMillionUsd: 0.5 },
  ratesCheckedAt: '2026-09-27', rateSource: 'https://provider.example/pricing', qualityScore: 80, qualityBenchmark: 'held-out graph audit v2', benchmarkDate: '2026-09-26', benchmarkSamples: 40,
  p95LatencyMs: 1200, maxContextTokens: 32000, maxOutputTokens: 4000, enabled: true, ...overrides,
});

test('unknown rates and unknown limits stay unranked instead of becoming zero-cost', () => {
  const item = createStarterCandidates().find(row => row.modelId === 'GPT-6 Astra')!;
  const result = assessCandidate(item, request());
  assert.equal(result.estimate?.costPerSuccessfulRunUsd, null);
  assert.ok(result.blockers.some(reason => reason.includes('Context limit is unknown')));
  assert.ok(result.estimate?.unpricedComponents.length);
  const plan = buildDelegationPlan({ request: request(), candidates: [item], now: '2026-09-27T00:00:00.000Z' });
  assert.equal(plan.recommendedCandidateId, null);
  assert.equal(plan.status, 'planned');
  assert.equal(plan.actualUsage, null);
  assert.equal(plan.invoiceStatus, 'not-reconciled');
});

test('hard constraints block unsupported capabilities and privacy routes', () => {
  const result = assessCandidate(candidate({ capabilities: ['coding'], privacy: 'provider-policy' }), request());
  assert.equal(result.eligible, false);
  assert.ok(result.blockers.some(reason => reason.includes('Capability not verified')));
  assert.ok(result.blockers.some(reason => reason.includes('No-training handling')));
});

test('best candidate is selected only among fully evidenced candidates and weights are explained', () => {
  const moreExpensive = candidate({ id: 'expensive', name: 'Expensive strong route', rates: { inputPerMillionUsd: 5, outputPerMillionUsd: 10, cacheReadPerMillionUsd: 1, cacheWritePerMillionUsd: 2 }, qualityScore: 96, p95LatencyMs: 2000 });
  const lowerCost = candidate({ id: 'low-cost', name: 'Low cost route', qualityScore: 85, p95LatencyMs: 900 });
  const plan = buildDelegationPlan({ request: request(), candidates: [moreExpensive, lowerCost], now: '2026-09-27T00:00:00.000Z' });
  assert.equal(plan.recommendedCandidateId, 'low-cost');
  const result = plan.candidates.find(item => item.candidate.id === 'low-cost')!;
  assert.ok(result.rankScore !== null);
  assert.match(result.rankExplanation, /held-out graph audit v2/);
  assert.match(plan.recommendation, /not a universal best-model claim/);
});

test('budget, benchmark and required-latency constraints prevent a recommendation', () => {
  const input = request(); input.perRunBudgetUsd = 0.00001;
  const plan = buildDelegationPlan({ request: input, candidates: [candidate()] });
  assert.equal(plan.recommendedCandidateId, null);
  assert.ok(plan.candidates[0].blockers.includes('Estimated per-run budget is exceeded.'));

  input.perRunBudgetUsd = null;
  const noLatency = buildDelegationPlan({ request: input, candidates: [candidate({ p95LatencyMs: null })] });
  assert.equal(noLatency.recommendedCandidateId, null);
  assert.match(noLatency.candidates[0].rankExplanation, /p95 latency is required/);

  const noBenchmark = buildDelegationPlan({ request: input, candidates: [candidate({ qualityScore: null, qualityBenchmark: '' })] });
  assert.equal(noBenchmark.recommendedCandidateId, null);
  assert.match(noBenchmark.candidates[0].rankExplanation, /dated benchmark/);

  const noRateProvenance = buildDelegationPlan({ request: input, candidates: [candidate({ ratesCheckedAt: '', rateSource: 'file:///etc/passwd' })] });
  assert.equal(noRateProvenance.recommendedCandidateId, null);
  assert.match(noRateProvenance.candidates[0].rankExplanation, /HTTP\(S\) provenance/);

  const noBenchmarkSamples = buildDelegationPlan({ request: input, candidates: [candidate({ benchmarkSamples: null })] });
  assert.equal(noBenchmarkSamples.recommendedCandidateId, null);
  assert.match(noBenchmarkSamples.candidates[0].rankExplanation, /positive sample count/);
});

test('custom model/API IDs remain extensible and plan assumptions preserve unknown subscription usage', () => {
  const custom = candidate({ modelId: 'my-private-endpoint/2026-09' });
  const input = request();
  const plan = buildDelegationPlan({ request: input, candidates: [custom] });
  assert.equal(plan.candidates[0].candidate.modelId, 'my-private-endpoint/2026-09');
  assert.equal(plan.executionStatus, 'not-started');

  const subscription = candidate({ provider: 'subscription', rates: { inputPerMillionUsd: null, outputPerMillionUsd: null, cacheReadPerMillionUsd: null, cacheWritePerMillionUsd: null } });
  const subPlan = buildDelegationPlan({ request: input, candidates: [subscription] });
  assert.equal(subPlan.candidates[0].estimate?.modelCostPerStartedRunUsd, null);
  assert.ok(subPlan.candidates[0].estimate?.unpricedComponents.includes('subscription quota or overage consumption per model run'));
});
