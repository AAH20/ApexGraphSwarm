import {
  calculateExecutionEconomics,
  type ExecutionEstimate,
  type TokenRates,
} from './execution-economics';
import { harnessCatalog, type HarnessId, type ProviderMode } from './harness-catalog';

export type PrivacyRequirement = 'any' | 'no-training' | 'local-only';
export type CandidatePrivacy = 'unknown' | 'provider-policy' | 'no-training' | 'local-only';
export type Candidate = {
  id: string;
  name: string;
  harnessId: HarnessId;
  provider: ProviderMode;
  modelId: string;
  capabilities: string[];
  privacy: CandidatePrivacy;
  rates: TokenRates;
  ratesCheckedAt: string;
  rateSource: string;
  qualityScore: number | null;
  qualityBenchmark: string;
  benchmarkDate: string;
  benchmarkSamples: number | null;
  p95LatencyMs: number | null;
  maxContextTokens: number | null;
  maxOutputTokens: number | null;
  enabled: boolean;
};

export type PlannerRequest = {
  taskClass: string;
  goal: string;
  requiredCapabilities: string[];
  privacyRequirement: PrivacyRequirement;
  inputTokens: number;
  outputTokens: number;
  cacheReadTokens: number;
  cacheWriteTokens: number;
  agents: number;
  retries: number;
  successRatePercent: number;
  plannedRunsPerMonth: number;
  monthlyBudgetUsd: number | null;
  perRunBudgetUsd: number | null;
  allocatedSubscriptionMonthlyUsd: number;
  subscriptionAllocationPercent: number;
  otherFixedMonthlyUsd: number;
  gpuRateUsdPerGpuHour: number | null;
  gpuHoursPerAttempt: number | null;
  gpuUtilizationPercent: number | null;
  weights: { cost: number; quality: number; latency: number };
};

export type CandidateAssessment = {
  candidate: Candidate;
  eligible: boolean;
  blockers: string[];
  estimate: ExecutionEstimate | null;
  rankScore: number | null;
  rankExplanation: string;
};

export type DelegationPlan = {
  schemaVersion: 1;
  createdAt: string;
  status: 'planned';
  task: { taskClass: string; goal: string; requiredCapabilities: string[]; privacyRequirement: PrivacyRequirement };
  assumptions: Omit<PlannerRequest, 'goal' | 'taskClass' | 'requiredCapabilities' | 'privacyRequirement'>;
  recommendedCandidateId: string | null;
  recommendation: string;
  candidates: CandidateAssessment[];
  executionStatus: 'not-started';
  actualUsage: null;
  invoiceStatus: 'not-reconciled';
};

const nullRates = (): TokenRates => ({ inputPerMillionUsd: null, outputPerMillionUsd: null, cacheReadPerMillionUsd: null, cacheWritePerMillionUsd: null });
const currentDate = '2026-09-27';

/** Seed with named options and verified reference cards; users must add evidence before ranking unknown routes. */
export function createStarterCandidates(): Candidate[] {
  const codexModelNames = ['GPT-6 Astra', 'GPT-6 Sol', 'GPT-6 Luna', 'GPT-5.6 Sol', 'GPT-5.6 Terra', 'GPT-5.6 Luna', 'GPT-5.5', 'GPT-Daybreak Blue'];
  const candidates: Candidate[] = codexModelNames.map((name, index) => ({
    id: `codex-${index}`,
    name: `Codex · ${name}`,
    harnessId: 'codex', provider: 'subscription', modelId: name,
    capabilities: [], privacy: 'unknown', rates: nullRates(), ratesCheckedAt: '', rateSource: '',
    qualityScore: null, qualityBenchmark: '', benchmarkDate: '', benchmarkSamples: null,
    p95LatencyMs: null, maxContextTokens: null, maxOutputTokens: null, enabled: true,
  }));
  const generic = harnessCatalog.filter(item => item.id !== 'codex').map(harness => ({
    id: `${harness.id}-custom`, name: `${harness.name} · custom route`, harnessId: harness.id,
    provider: harness.providers.includes('subscription') ? 'subscription' as const : 'manual' as const,
    modelId: '', capabilities: [], privacy: 'unknown' as const, rates: nullRates(), ratesCheckedAt: '', rateSource: '',
    qualityScore: null, qualityBenchmark: '', benchmarkDate: '', benchmarkSamples: null,
    p95LatencyMs: null, maxContextTokens: null, maxOutputTokens: null, enabled: true,
  }));
  const verifiedOpenRouter: Candidate[] = [
    { id: 'or-gpt-5.6-sol', name: 'OpenAI GPT-5.6 Sol · OpenRouter', harnessId: 'opencode', provider: 'openrouter', modelId: 'openai/gpt-5.6-sol', capabilities: ['coding'], privacy: 'unknown', rates: { inputPerMillionUsd: 1, outputPerMillionUsd: 6, cacheReadPerMillionUsd: 0.1, cacheWritePerMillionUsd: null }, ratesCheckedAt: '2026-09-27', rateSource: 'https://openrouter.ai/api/v1/models', qualityScore: null, qualityBenchmark: '', benchmarkDate: '', benchmarkSamples: null, p95LatencyMs: null, maxContextTokens: 272000, maxOutputTokens: null, enabled: true },
    { id: 'or-claude-opus-4.6', name: 'Claude Opus 4.6 · OpenRouter', harnessId: 'opencode', provider: 'openrouter', modelId: 'anthropic/claude-opus-4.6', capabilities: ['coding', 'reasoning'], privacy: 'unknown', rates: { inputPerMillionUsd: 5, outputPerMillionUsd: 25, cacheReadPerMillionUsd: 0.5, cacheWritePerMillionUsd: 6.25 }, ratesCheckedAt: '2026-09-27', rateSource: 'https://openrouter.ai/api/v1/models', qualityScore: null, qualityBenchmark: '', benchmarkDate: '', benchmarkSamples: null, p95LatencyMs: null, maxContextTokens: null, maxOutputTokens: null, enabled: true },
    { id: 'or-qwen3.6-35b', name: 'Qwen3.6 35B A3B · OpenRouter', harnessId: 'opencode', provider: 'openrouter', modelId: 'qwen/qwen3.6-35b-a3b', capabilities: ['coding'], privacy: 'unknown', rates: { inputPerMillionUsd: 0.15, outputPerMillionUsd: 1, cacheReadPerMillionUsd: 0.05, cacheWritePerMillionUsd: null }, ratesCheckedAt: '2026-09-27', rateSource: 'https://openrouter.ai/api/v1/models', qualityScore: null, qualityBenchmark: '', benchmarkDate: '', benchmarkSamples: null, p95LatencyMs: null, maxContextTokens: null, maxOutputTokens: null, enabled: true },
  ];
  return [...candidates, ...generic, ...verifiedOpenRouter];
}

function estimateFor(candidate: Candidate, request: PlannerRequest): ExecutionEstimate {
  return calculateExecutionEconomics({
    harnessId: candidate.harnessId,
    provider: candidate.provider,
    rates: candidate.rates,
    uncachedInputTokensPerAgentAttempt: request.inputTokens,
    outputTokensPerAgentAttempt: request.outputTokens,
    cacheReadTokensPerAgentAttempt: request.cacheReadTokens,
    cacheWriteTokensPerAgentAttempt: request.cacheWriteTokens,
    agentsPerRun: request.agents,
    retriesPerAgent: request.retries,
    successRatePercent: request.successRatePercent,
    plannedRunsPerMonth: request.plannedRunsPerMonth,
    allocatedSubscriptionMonthlyUsd: request.allocatedSubscriptionMonthlyUsd,
    subscriptionAllocationPercent: request.subscriptionAllocationPercent,
    otherFixedMonthlyUsd: request.otherFixedMonthlyUsd,
    reservedGpuMonthlyUsd: 0,
    gpuRateUsdPerGpuHour: candidate.provider === 'vllm' ? request.gpuRateUsdPerGpuHour : null,
    gpuCount: 1,
    gpuWallClockHoursPerAgentAttempt: candidate.provider === 'vllm' ? request.gpuHoursPerAttempt : null,
    gpuUtilizationPercent: candidate.provider === 'vllm' ? request.gpuUtilizationPercent : null,
    revenuePerSuccessfulRunUsd: null,
    perRunBudgetUsd: request.perRunBudgetUsd,
    monthlyBudgetUsd: request.monthlyBudgetUsd,
  });
}

function candidateBlockers(candidate: Candidate, request: PlannerRequest): string[] {
  const blockers: string[] = [];
  if (!candidate.enabled) blockers.push('Candidate is disabled.');
  const provided = new Set(candidate.capabilities.map(value => value.trim().toLowerCase()).filter(Boolean));
  for (const capability of request.requiredCapabilities) {
    if (!provided.has(capability.toLowerCase())) blockers.push(`Capability not verified: ${capability}.`);
  }
  if (request.privacyRequirement === 'local-only' && candidate.privacy !== 'local-only') blockers.push('Local-only privacy is required, but this route is not verified local.');
  if (request.privacyRequirement === 'no-training' && !['no-training', 'local-only'].includes(candidate.privacy)) blockers.push('No-training handling is required, but this route is not verified.');
  const context = request.inputTokens + request.outputTokens;
  if (candidate.maxContextTokens === null) blockers.push('Context limit is unknown.');
  else if (context > candidate.maxContextTokens) blockers.push(`Context limit too small (${candidate.maxContextTokens} tokens).`);
  if (candidate.maxOutputTokens === null) blockers.push('Output limit is unknown.');
  else if (request.outputTokens > candidate.maxOutputTokens) blockers.push(`Output limit too small (${candidate.maxOutputTokens} tokens).`);
  return blockers;
}

export function assessCandidate(candidate: Candidate, request: PlannerRequest): CandidateAssessment {
  const blockers = candidateBlockers(candidate, request);
  let estimate: ExecutionEstimate | null = null;
  try { estimate = estimateFor(candidate, request); }
  catch (error) { blockers.push(error instanceof Error ? error.message : 'Invalid planning assumptions.'); }
  if (estimate?.perRunBudgetStatus === 'exceeds') blockers.push('Estimated per-run budget is exceeded.');
  if (estimate?.monthlyBudgetStatus === 'exceeds') blockers.push('Estimated monthly budget is exceeded.');
  return { candidate, eligible: blockers.length === 0, blockers, estimate, rankScore: null, rankExplanation: '' };
}

export function buildDelegationPlan(input: {
  request: PlannerRequest;
  candidates: Candidate[];
  now?: string;
}): DelegationPlan {
  const { request } = input;
  const candidates = input.candidates.map(candidate => assessCandidate(candidate, request));
  const eligible = candidates.filter(item => item.eligible);
  const weightsTotal = request.weights.cost + request.weights.quality + request.weights.latency;
  const weightsValid = [request.weights.cost, request.weights.quality, request.weights.latency].every(value => Number.isFinite(value) && value >= 0) && weightsTotal > 0;
  const ranked = eligible.filter(item => {
    if (item.estimate?.costPerSuccessfulRunUsd === null || item.estimate?.costPerSuccessfulRunUsd === undefined) {
      item.rankExplanation = 'Not ranked: route cost or expected success cost is unknown.';
      return false;
    }
    if (item.candidate.qualityScore === null || !item.candidate.qualityBenchmark.trim()) {
      item.rankExplanation = 'Not ranked: add a dated benchmark score and benchmark name.';
      return false;
    }
    if (!item.candidate.benchmarkDate || item.candidate.benchmarkSamples === null || item.candidate.benchmarkSamples < 1) {
      item.rankExplanation = 'Not ranked: benchmark date and positive sample count are required.';
      return false;
    }
    if (!item.candidate.ratesCheckedAt || !isHttpSource(item.candidate.rateSource)) {
      item.rankExplanation = 'Not ranked: add the rate/hosting quote date and an HTTP(S) provenance source.';
      return false;
    }
    if (request.weights.latency > 0 && item.candidate.p95LatencyMs === null) {
      item.rankExplanation = 'Not ranked: p95 latency is required by the selected latency weight.';
      return false;
    }
    return true;
  });

  if (!weightsValid) for (const item of ranked) item.rankExplanation = 'Not ranked: ranking weights must be non-negative and sum above zero.';
  if (weightsValid && ranked.length) {
    const costs = ranked.map(item => item.estimate!.costPerSuccessfulRunUsd!);
    const qualities = ranked.map(item => item.candidate.qualityScore!);
    const latencies = request.weights.latency > 0 ? ranked.map(item => item.candidate.p95LatencyMs!) : [];
    const minMax = (values: number[], value: number, reverse = false) => {
      const min = Math.min(...values); const max = Math.max(...values);
      if (min === max) return 1;
      const normalized = (value - min) / (max - min);
      return reverse ? normalized : 1 - normalized;
    };
    for (const item of ranked) {
      const score = request.weights.cost * minMax(costs, item.estimate!.costPerSuccessfulRunUsd!) +
        request.weights.quality * minMax(qualities, item.candidate.qualityScore!, true) +
        (request.weights.latency > 0 ? request.weights.latency * minMax(latencies, item.candidate.p95LatencyMs!) : 0);
      item.rankScore = score / weightsTotal;
      item.rankExplanation = `Score ${item.rankScore.toFixed(3)} from configured cost, benchmark-quality, and latency weights; benchmark ${item.candidate.qualityBenchmark} (${item.candidate.benchmarkDate || 'date missing'}).`;
    }
  }
  const winner = weightsValid ? ranked.sort((a, b) => (b.rankScore ?? -1) - (a.rankScore ?? -1))[0] : undefined;
  const recommendation = winner
    ? `${winner.candidate.name} ranks highest among eligible, benchmarked candidates under these editable weights. This is a task-specific plan, not a universal best-model claim.`
    : eligible.length
      ? 'No recommendation yet: eligible routes still need known price, dated benchmark quality, and the measurements required by the chosen ranking weights.'
      : 'No eligible route: satisfy the capability, privacy, context, output, and budget constraints or add a verified candidate.';
  return {
    schemaVersion: 1,
    createdAt: input.now ?? new Date().toISOString(),
    status: 'planned',
    task: { taskClass: request.taskClass, goal: request.goal, requiredCapabilities: [...request.requiredCapabilities], privacyRequirement: request.privacyRequirement },
    assumptions: {
      inputTokens: request.inputTokens, outputTokens: request.outputTokens, cacheReadTokens: request.cacheReadTokens,
      cacheWriteTokens: request.cacheWriteTokens, agents: request.agents, retries: request.retries,
      successRatePercent: request.successRatePercent, plannedRunsPerMonth: request.plannedRunsPerMonth,
      monthlyBudgetUsd: request.monthlyBudgetUsd, perRunBudgetUsd: request.perRunBudgetUsd,
      allocatedSubscriptionMonthlyUsd: request.allocatedSubscriptionMonthlyUsd,
      subscriptionAllocationPercent: request.subscriptionAllocationPercent, otherFixedMonthlyUsd: request.otherFixedMonthlyUsd,
      gpuRateUsdPerGpuHour: request.gpuRateUsdPerGpuHour, gpuHoursPerAttempt: request.gpuHoursPerAttempt,
      gpuUtilizationPercent: request.gpuUtilizationPercent, weights: { ...request.weights },
    },
    recommendedCandidateId: winner?.candidate.id ?? null,
    recommendation,
    candidates,
    executionStatus: 'not-started', actualUsage: null, invoiceStatus: 'not-reconciled',
  };
}

function isHttpSource(value: string): boolean {
  try {
    const url = new URL(value);
    return url.protocol === 'http:' || url.protocol === 'https:';
  } catch { return false; }
}

export function candidateWithRate(candidate: Candidate, key: keyof TokenRates, value: number | null): Candidate {
  return { ...candidate, rates: { ...candidate.rates, [key]: value } };
}
