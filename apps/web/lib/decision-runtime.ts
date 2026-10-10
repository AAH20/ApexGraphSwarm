import type {
  DecisionAnswer,
  DecisionInput,
  DecisionProvider,
  DecisionQuestion,
  DecisionResult,
  ProviderInfo,
} from './decision-types';

const LIMITS = {
  stateChars: 16_000,
  questions: 8,
  instructionsChars: 1_000,
  labelChars: 80,
  requestBytes: 64 * 1024,
  responseBytes: 256 * 1024,
  timeoutMs: 15_000,
} as const;
const MAX_SAFE = Number.MAX_SAFE_INTEGER;
const PROVIDERS: Record<DecisionProvider, {label: string; urlKey: string; tokenKey: string; costKey: string}> = {
  laya: {label: 'Laya', urlKey: 'LAYA_PREDICT_URL', tokenKey: 'LAYA_API_KEY', costKey: 'LAYA_COST_MICROUSD_PER_QUESTION'},
  anyjev: {label: 'AnyJev L0 bridge', urlKey: 'ANYJEV_PREDICT_URL', tokenKey: 'ANYJEV_API_KEY', costKey: 'ANYJEV_COST_MICROUSD_PER_QUESTION'},
};
const COVERAGE_WARNING = 'Provider context/token limits may truncate this input; repository-wide coverage is unverified.';
const DANGEROUS_KEYS = new Set(['__proto__', 'prototype', 'constructor']);

/**
 * Type RuntimeEnv.
 *
 *
 * @example
 * ```typescript
 * import { RuntimeEnv } from './module';
 * ```
 */
type RuntimeEnv = Record<string, string | undefined>;
/**
 * Type Fetcher.
 *
 *
 * @example
 * ```typescript
 * import { Fetcher } from './module';
 * ```
 */
type Fetcher = typeof fetch;
/**
 * Type ProviderConfig.
 *
 *
 * @example
 * ```typescript
 * import { ProviderConfig } from './module';
 * ```
 */
type ProviderConfig = {url: string; token: string; cost: number};
/**
 * Type NormalizedProviderAnswer.
 *
 *
 * @example
 * ```typescript
 * import { NormalizedProviderAnswer } from './module';
 * ```
 */
type NormalizedProviderAnswer = Omit<DecisionAnswer, 'id' | 'reviewRequired'>;

/**
 * Class DecisionRuntimeError.
 *
 * @extends Error
 *
 * @example
 * ```typescript
 * const instance = new DecisionRuntimeError();
 * ```
 */
export class DecisionRuntimeError extends Error {
  constructor(message: string) { super(message); this.name = 'DecisionRuntimeError'; }
}

/**
 * Function isRecord.
 *
 * @param value - Description of value.
 * @returns {value is Record<string, unknown>} Description of return value.
 *
 * @example
 * ```typescript
 * const result = isRecord(...);
 * ```
 */
function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}
/**
 * Function exactKeys.
 *
 * @param {Record<string, unknown>} value - Description of value.
 * @param {string[]} required - Description of required.
 * @param {string[]} optional - Description of optional.
 * @returns {boolean} Description of return value.
 *
 * @example
 * ```typescript
 * const result = exactKeys(..., ..., ...);
 * ```
 */
function exactKeys(value: Record<string, unknown>, required: string[], optional: string[] = []): boolean {
  const keys = Object.keys(value);
  return required.every(key => Object.hasOwn(value, key)) && keys.every(key => required.includes(key) || optional.includes(key));
}
/**
 * Function safeInteger.
 *
 * @param value - Description of value.
 * @returns {value is number} Description of return value.
 *
 * @example
 * ```typescript
 * const result = safeInteger(...);
 * ```
 */
function safeInteger(value: unknown): value is number {
  return typeof value === 'number' && Number.isSafeInteger(value) && value >= 0;
}
/**
 * Function cleanString.
 *
 * @param value - Description of value.
 * @param {number} max - Description of max.
 * @param allowEmpty - Description of allowEmpty.
 * @returns {value is string} Description of return value.
 *
 * @example
 * ```typescript
 * const result = cleanString(..., ..., ...);
 * ```
 */
function cleanString(value: unknown, max: number, allowEmpty = false): value is string {
  return typeof value === 'string' && value.length <= max && (allowEmpty || value.trim().length > 0);
}
/**
 * Function criteriaLabels.
 *
 * @param {DecisionQuestion} question - Description of question.
 * @returns {string[] | null} Description of return value.
 *
 * @example
 * ```typescript
 * const result = criteriaLabels(...);
 * ```
 */
function criteriaLabels(question: DecisionQuestion): string[] | null {
  if (Array.isArray(question.criteria)) return question.criteria as string[];
  if (isRecord(question.criteria)) return Object.keys(question.criteria);
  return null;
}

/**
 * Function validateDecisionInput.
 *
 * @param raw - Description of raw.
 * @returns {DecisionInput} Description of return value.
 *
 * @example
 * ```typescript
 * const result = validateDecisionInput(...);
 * ```
 */
export function validateDecisionInput(raw: unknown): DecisionInput {
  if (!isRecord(raw) || !exactKeys(raw, ['providers', 'state', 'questions', 'threshold', 'maxCostMicrousd'])) {
    throw new DecisionRuntimeError('Request must contain only providers, state, questions, threshold, and maxCostMicrousd.');
  }
  if (!Array.isArray(raw.providers) || raw.providers.length < 1 || raw.providers.length > 2 ||
      raw.providers.some(id => id !== 'laya' && id !== 'anyjev') || new Set(raw.providers).size !== raw.providers.length) {
    throw new DecisionRuntimeError('Choose one or two distinct supported providers.');
  }
  if (!cleanString(raw.state, LIMITS.stateChars)) throw new DecisionRuntimeError('State must be non-empty and at most 16,000 characters.');
  if (typeof raw.threshold !== 'number' || !Number.isFinite(raw.threshold) || raw.threshold < 0 || raw.threshold > 1) {
    throw new DecisionRuntimeError('threshold must be a finite number from 0 to 1.');
  }
  if (!safeInteger(raw.maxCostMicrousd)) throw new DecisionRuntimeError('maxCostMicrousd must be a non-negative safe integer.');
  if (!isRecord(raw.questions)) throw new DecisionRuntimeError('questions must be an object keyed by question id.');
  const questionEntries = Object.entries(raw.questions);
  if (questionEntries.length < 1 || questionEntries.length > LIMITS.questions) throw new DecisionRuntimeError('Provide between one and eight questions.');
  const questions: Record<string, DecisionQuestion> = {};
  for (const [id, value] of questionEntries) {
    if (!/^[A-Za-z][A-Za-z0-9_-]{0,79}$/.test(id) || DANGEROUS_KEYS.has(id) || !isRecord(value) || !exactKeys(value, ['type', 'instructions'], ['criteria'])) {
      throw new DecisionRuntimeError('Each question needs a valid id, type, instructions, and optional criteria.');
    }
    if (value.type !== 'choice' && value.type !== 'score' && value.type !== 'noul') throw new DecisionRuntimeError(`Question ${id} has an unsupported type.`);
    const questionType = value.type as DecisionQuestion['type'];
    if (!cleanString(value.instructions, LIMITS.instructionsChars)) throw new DecisionRuntimeError(`Question ${id} instructions must be non-empty and at most 1,000 characters.`);
    let criteria: DecisionQuestion['criteria'];
    if (value.criteria !== undefined) {
      if (Array.isArray(value.criteria)) {
        if (value.criteria.length < 2 || value.criteria.length > 12 || value.criteria.some(label => !cleanString(label, LIMITS.labelChars) || DANGEROUS_KEYS.has(label)) || new Set(value.criteria).size !== value.criteria.length) {
          throw new DecisionRuntimeError(`Question ${id} criteria must contain two to twelve labels of at most 80 characters.`);
        }
        criteria = [...value.criteria] as string[];
      } else if (isRecord(value.criteria)) {
        const entries = Object.entries(value.criteria);
        if (entries.length < 2 || entries.length > 12 || entries.some(([label, description]) => !cleanString(label, LIMITS.labelChars) || DANGEROUS_KEYS.has(label) || !cleanString(description, 500))) {
          throw new DecisionRuntimeError(`Question ${id} criteria must contain two to twelve bounded labels and descriptions.`);
        }
        criteria = Object.fromEntries(entries) as Record<string, string>;
      } else throw new DecisionRuntimeError(`Question ${id} criteria must be a label list or label-description object.`);
    }
    if ((questionType === 'choice' || questionType === 'score') && !criteria) throw new DecisionRuntimeError(`Question ${id} requires explicit criteria.`);
    if (questionType === 'noul' && criteria && (criteriaLabels({type: questionType, instructions: '', criteria})?.length !== 2 || !criteriaLabels({type: questionType, instructions: '', criteria})?.includes('false') || !criteriaLabels({type: questionType, instructions: '', criteria})?.includes('true'))) {
      throw new DecisionRuntimeError(`Question ${id} noul criteria, when provided, must be false and true.`);
    }
    questions[id] = {type: questionType, instructions: value.instructions, ...(criteria ? {criteria} : {})} as DecisionQuestion;
  }
  const result: DecisionInput = {providers: raw.providers as DecisionProvider[], state: raw.state, questions, threshold: raw.threshold, maxCostMicrousd: raw.maxCostMicrousd};
  if (new TextEncoder().encode(JSON.stringify(result)).byteLength > LIMITS.requestBytes) throw new DecisionRuntimeError('Validated request exceeds 64 KiB.');
  return result;
}

/**
 * Function parseEstimate.
 *
 * @param {string | undefined} raw - Description of raw.
 * @returns {number | null} Description of return value.
 *
 * @example
 * ```typescript
 * const result = parseEstimate(...);
 * ```
 */
function parseEstimate(raw: string | undefined): number | null {
  if (raw === undefined || !/^(0|[1-9][0-9]*)$/.test(raw)) return null;
  const estimate = Number(raw);
  return safeInteger(estimate) ? estimate : null;
}

/**
 * Function allowedEndpoint.
 *
 * @param {string | undefined} raw - Description of raw.
 * @returns {string | null} Description of return value.
 *
 * @example
 * ```typescript
 * const result = allowedEndpoint(...);
 * ```
 */
function allowedEndpoint(raw: string | undefined): string | null {
  if (!raw || raw.length > 2_048) return null;
  try {
    const url = new URL(raw);
    const loopback = url.hostname === 'localhost' || url.hostname === '127.0.0.1' || url.hostname === '[::1]';
    if ((url.protocol !== 'https:' && !(url.protocol === 'http:' && loopback)) || url.username || url.password || url.hash) return null;
    return url.toString();
  } catch { return null; }
}

/**
 * Function providerConfig.
 *
 * @param {DecisionProvider} provider - Description of provider.
 * @param {RuntimeEnv} env - Description of env.
 * @returns {ProviderConfig | null} Description of return value.
 *
 * @example
 * ```typescript
 * const result = providerConfig(..., ...);
 * ```
 */
function providerConfig(provider: DecisionProvider, env: RuntimeEnv): ProviderConfig | null {
  const keys = PROVIDERS[provider];
  const url = allowedEndpoint(env[keys.urlKey]);
  const token = env[keys.tokenKey];
  const cost = parseEstimate(env[keys.costKey]);
  if (!url || !token || token.length > 4_096 || cost === null) return null;
  return {url, token, cost};
}

/**
 * Function getDecisionProviders.
 *
 * @param {RuntimeEnv} env - Description of env.
 * @returns {ProviderInfo[]} Description of return value.
 *
 * @example
 * ```typescript
 * const result = getDecisionProviders(...);
 * ```
 */
export function getDecisionProviders(env: RuntimeEnv = process.env): ProviderInfo[] {
  return (['laya', 'anyjev'] as const).map(id => {
    const config = providerConfig(id, env);
    return {
      id,
      label: PROVIDERS[id].label,
      configured: config !== null,
      statusText: config ? `Configured · estimate ${config.cost} µUSD per question; actual cost is not reported.` : 'Not configured · set a server endpoint, bearer token, and conservative cost estimate.',
      estimatedCostPerQuestionMicrousd: config?.cost ?? null,
    };
  });
}

/**
 * Function validProbability.
 *
 * @param value - Description of value.
 * @returns {value is number} Description of return value.
 *
 * @example
 * ```typescript
 * const result = validProbability(...);
 * ```
 */
function validProbability(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 1;
}
/**
 * Function validateDistribution.
 *
 * @param value - Description of value.
 * @param {string[]} labels - Description of labels.
 * @returns {Record<string, number> | null} Description of return value.
 *
 * @example
 * ```typescript
 * const result = validateDistribution(..., ...);
 * ```
 */
function validateDistribution(value: unknown, labels?: string[]): Record<string, number> | null {
  if (!isRecord(value)) return null;
  const entries = Object.entries(value);
  if (entries.length < 1 || entries.length > 12 || entries.some(([key, probability]) => !cleanString(key, 80) || !validProbability(probability))) return null;
  if (labels && (entries.length !== labels.length || labels.some(label => !Object.hasOwn(value, label)))) return null;
  const sum = entries.reduce((total, [, probability]) => total + (probability as number), 0);
  if (Math.abs(sum - 1) > 0.025) return null;
  return Object.fromEntries(entries) as Record<string, number>;
}
/**
 * Function normalizeAnswer.
 *
 * @param raw - Description of raw.
 * @param {DecisionQuestion} question - Description of question.
 * @returns {NormalizedProviderAnswer | null} Description of return value.
 *
 * @example
 * ```typescript
 * const result = normalizeAnswer(..., ...);
 * ```
 */
function normalizeAnswer(raw: unknown, question: DecisionQuestion): NormalizedProviderAnswer | null {
  if (!isRecord(raw)) return null;
  if (raw.type !== question.type) return null;
  const type = question.type;
  // AnyJev bridge normalized answer envelope.
  if (exactKeys(raw, ['type', 'value', 'confidence', 'distribution'])) {
    if (!validProbability(raw.confidence)) return null;
    const labels = criteriaLabels(question) ?? (question.type === 'noul' ? ['false', 'true'] : undefined);
    const distribution = validateDistribution(raw.distribution, labels);
    if (!distribution) return null;
    if (question.type === 'choice') {
      if (typeof raw.value !== 'string' || !labels?.includes(raw.value)) return null;
      if (Math.abs(raw.confidence - distribution[raw.value]) > 0.025) return null;
    } else if (question.type === 'score') {
      const max = (labels?.length ?? 1) - 1;
      if (typeof raw.value !== 'number' || !Number.isFinite(raw.value) || raw.value < 0 || raw.value > max) return null;
      if (Math.abs(raw.confidence - Math.max(...Object.values(distribution))) > 0.025) return null;
      const expected = (labels ?? []).reduce((total, label, index) => total + index * distribution[label], 0);
      if (Math.abs(raw.value - expected) > 0.025) return null;
    } else if (!validProbability(raw.value)) return null;
    if (question.type === 'noul' && Math.abs(raw.confidence - Math.max(...Object.values(distribution))) > 0.025) return null;
    return {type, value: raw.value as string | number, confidence: raw.confidence, distribution};
  }
  // Laya /v1/systemone native answer fields.
  if (question.type === 'choice') {
    const labels = criteriaLabels(question)!;
    if (!cleanString(raw.choice, LIMITS.labelChars) || !labels.includes(raw.choice) || !validProbability(raw.answer_confidence ?? raw.confidence)) return null;
    const distribution = validateDistribution(raw.probabilities, labels);
    const confidence = (raw.answer_confidence ?? raw.confidence) as number;
    return distribution && Math.abs(confidence - distribution[raw.choice]) <= 0.025 ? {type, value: raw.choice, confidence, distribution} : null;
  }
  if (question.type === 'score') {
    const labels = criteriaLabels(question)!;
    if (typeof raw.score !== 'number' || !Number.isFinite(raw.score) || raw.score < 0 || raw.score > labels.length - 1 || !validProbability(raw.answer_confidence ?? raw.confidence)) return null;
    const probs = validateDistribution(raw.probabilities, Array.from({length: labels.length}, (_, index) => String(index)));
    if (!probs) return null;
    const distribution = Object.fromEntries(Object.entries(probs).map(([index, probability]) => [labels[Number(index)], probability]));
    const confidence = (raw.answer_confidence ?? raw.confidence) as number;
    if (Math.abs(confidence - Math.max(...Object.values(distribution))) > 0.025) return null;
    const expected = labels.reduce((total, label, index) => total + index * distribution[label], 0);
    if (Math.abs(raw.score - expected) > 0.025) return null;
    return {type, value: raw.score, confidence, distribution};
  }
  if (!validProbability(raw.noul) || !validProbability(raw.answer_confidence ?? raw.confidence)) return null;
  const probability = raw.noul;
  const confidence = (raw.answer_confidence ?? raw.confidence) as number;
  if (Math.abs(confidence - Math.max(probability, 1 - probability)) > 0.025) return null;
  return {type, value: probability, confidence, distribution: {false: 1 - probability, true: probability}};
}

/**
 * Function normalizeResponse.
 *
 * @param payload - Description of payload.
 * @param {DecisionInput} input - Description of input.
 *
 * @example
 * ```typescript
 * const result = normalizeResponse(..., ...);
 * ```
 */
function normalizeResponse(payload: unknown, input: DecisionInput): {model: string | null; answers: DecisionAnswer[]} | null {
  if (!isRecord(payload) || !isRecord(payload.answers)) return null;
  const questionIds = Object.keys(input.questions);
  if (Object.keys(payload.answers).length !== questionIds.length || questionIds.some(id => !Object.hasOwn(payload.answers as object, id))) return null;
  if (payload.model !== undefined && payload.model !== null && !cleanString(payload.model, 120)) return null;
  const answers: DecisionAnswer[] = [];
  for (const id of questionIds) {
    const normalized = normalizeAnswer(payload.answers[id], input.questions[id]);
    if (!normalized) return null;
    answers.push({...normalized, id, reviewRequired: normalized.confidence < input.threshold});
  }
  return {model: typeof payload.model === 'string' ? payload.model : null, answers};
}

/**
 * Function readBoundedResponse.
 *
 * @param {Response} response - Description of response.
 * @returns {Promise<unknown>} Description of return value.
 *
 * @example
 * ```typescript
 * const result = readBoundedResponse(...);
 * ```
 */
async function readBoundedResponse(response: Response): Promise<unknown> {
  const contentLength = response.headers.get('content-length');
  if (contentLength && (!/^\d+$/.test(contentLength) || Number(contentLength) > LIMITS.responseBytes)) throw new Error('response-too-large');
  if (!response.body) throw new Error('empty-response');
  const reader = response.body.getReader();
  const chunks: Uint8Array[] = [];
  let total = 0;
  try {
    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      total += value.byteLength;
      if (total > LIMITS.responseBytes) {
        await reader.cancel();
        throw new Error('response-too-large');
      }
      chunks.push(value);
    }
  } finally { reader.releaseLock(); }
  const bytes = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
  return JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(bytes));
}

/**
 * Function baseResult.
 *
 * @param {DecisionProvider} provider - Description of provider.
 * @param {DecisionResult['status']} status - Description of status.
 * @param {number | null} estimate - Description of estimate.
 * @param {string} warning - Description of warning.
 * @param {string} error - Description of error.
 * @returns {DecisionResult} Description of return value.
 *
 * @example
 * ```typescript
 * const result = baseResult(..., ..., ..., ..., ...);
 * ```
 */
function baseResult(provider: DecisionProvider, status: DecisionResult['status'], estimate: number | null, warning: string, error?: string): DecisionResult {
  return {provider, status, answers: [], elapsedMs: 0, estimatedCostMicrousd: estimate, actualCostMicrousd: null, model: null, ...(error ? {error} : {}), warnings: warning ? [warning] : []};
}

/**
 * Function callProvider.
 *
 * @param {DecisionProvider} provider - Description of provider.
 * @param {ProviderConfig} config - Description of config.
 * @param {DecisionInput} input - Description of input.
 * @param {Fetcher} fetcher - Description of fetcher.
 * @returns {Promise<DecisionResult>} Description of return value.
 *
 * @example
 * ```typescript
 * const result = callProvider(..., ..., ..., ...);
 * ```
 */
async function callProvider(provider: DecisionProvider, config: ProviderConfig, input: DecisionInput, fetcher: Fetcher): Promise<DecisionResult> {
  const started = Date.now();
  const estimate = config.cost * Object.keys(input.questions).length;
  const warning = `${COVERAGE_WARNING} Estimated cost is an operator estimate; actual cost is unknown. A successful decision is not an authorization or safety guarantee.`;
  const body = JSON.stringify({state: input.state, questions: input.questions});
  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, LIMITS.timeoutMs);
  try {
    const fetchPromise = fetcher(config.url, {
      method: 'POST',
      headers: {'content-type': 'application/json', authorization: `Bearer ${config.token}`},
      body,
      redirect: 'manual',
      cache: 'no-store',
      signal: controller.signal,
    });
    const response = await Promise.race([
      fetchPromise,
      new Promise<never>((_, reject) => controller.signal.addEventListener('abort', () => reject(new Error('timeout')), {once: true})),
    ]);
    if (response.status >= 300 && response.status < 400) return {...baseResult(provider, 'failed', estimate, warning, 'Provider redirects are not followed.'), elapsedMs: Math.max(0, Date.now() - started)};
    if (!response.ok) return {...baseResult(provider, 'failed', estimate, warning, `Provider returned HTTP ${response.status}.`), elapsedMs: Math.max(0, Date.now() - started)};
    let payload: unknown;
    try { payload = await readBoundedResponse(response); }
    catch (error) {
      const reason = timedOut ? 'Provider request timed out after 15 seconds.' : error instanceof SyntaxError ? 'Provider response was not valid JSON.' : error instanceof Error && error.message === 'response-too-large' ? 'Provider response exceeded 256 KiB.' : 'Provider response could not be read safely.';
      return {...baseResult(provider, 'failed', estimate, warning, reason), elapsedMs: Math.max(0, Date.now() - started)};
    }
    const normalized = normalizeResponse(payload, input);
    if (!normalized) return {...baseResult(provider, 'failed', estimate, warning, 'Provider response did not match the requested typed questions.'), elapsedMs: Math.max(0, Date.now() - started)};
    return {provider, status: 'succeeded', answers: normalized.answers, elapsedMs: Math.max(0, Date.now() - started), estimatedCostMicrousd: estimate, actualCostMicrousd: null, model: normalized.model, warnings: [warning]};
  } catch {
    return {...baseResult(provider, 'failed', estimate, warning, timedOut ? 'Provider request timed out after 15 seconds.' : 'Provider request failed; it may have processed the request, so actual cost remains unknown.'), elapsedMs: Math.max(0, Date.now() - started)};
  } finally { clearTimeout(timer); }
}

/**
 * Function runDecisions.
 *
 * @param {DecisionInput | unknown} raw - Description of raw.
 * @param {RuntimeEnv} env - Description of env.
 * @param {Fetcher} fetcher - Description of fetcher.
 * @returns {Promise<DecisionResult[]>} Description of return value.
 *
 * @example
 * ```typescript
 * const result = runDecisions(..., ..., ...);
 * ```
 */
export async function runDecisions(raw: DecisionInput | unknown, env: RuntimeEnv = process.env, fetcher: Fetcher = fetch): Promise<DecisionResult[]> {
  const input = validateDecisionInput(raw);
  const configs = new Map<DecisionProvider, ProviderConfig | null>();
  let totalEstimate = 0;
  for (const provider of input.providers) {
    const config = providerConfig(provider, env);
    configs.set(provider, config);
    if (config) {
      const estimate = config.cost * Object.keys(input.questions).length;
      if (!Number.isSafeInteger(estimate) || !Number.isSafeInteger(totalEstimate + estimate)) {
        return input.providers.map(id => baseResult(id, 'failed', null, '', 'Estimated cost exceeds the supported safe-integer range.'));
      }
      totalEstimate += estimate;
    }
  }
  if (totalEstimate > input.maxCostMicrousd) {
    return input.providers.map(provider => {
      const config = configs.get(provider);
      const estimate = config ? config.cost * Object.keys(input.questions).length : null;
      return baseResult(provider, 'failed', estimate, '', 'Estimated total exceeds maxCostMicrousd; no provider was called.');
    });
  }
  return Promise.all(input.providers.map(provider => {
    const config = configs.get(provider);
    if (!config) return Promise.resolve(baseResult(provider, 'unconfigured', null, 'No provider call was made. Configure a server endpoint, bearer token, and cost estimate.'));
    return callProvider(provider, config, input, fetcher);
  }));
}

/**
 * Constant decisionRuntimeLimits.
 *
 *
 * @example
 * ```typescript
 * import { decisionRuntimeLimits } from './module';
 * ```
 */
export const decisionRuntimeLimits = Object.freeze({...LIMITS});
