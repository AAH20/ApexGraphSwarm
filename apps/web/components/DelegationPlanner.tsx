/**
 * React component for delegation planner.
 *
 * @module DelegationPlanner
 * @packageDocumentation
 */
'use client';

import { useMemo, useState } from 'react';
import { buildDelegationPlan, candidateWithRate, createStarterCandidates, type Candidate, type PrivacyRequirement } from '@/lib/delegation-planner';
import { harnessCatalog, type HarnessId, type ProviderMode } from '@/lib/harness-catalog';
import styles from './DelegationPlanner.module.css';

const numberOrNull = (value: string) => value.trim() === '' ? null : Number(value);
const valueOrEmpty = (value: number | null) => value === null ? '' : String(value);
const money = (value: number | null | undefined) => value === null || value === undefined ? 'Unknown' : new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 6 }).format(value);
const starters = createStarterCandidates();

/**
 * React component DelegationPlanner.
 *
 *
 * @example
 * ```typescript
 * import { DelegationPlanner } from './module';
 * ```
 */
export default function DelegationPlanner() {
  const [taskClass, setTaskClass] = useState('repository-analysis');
  const [goal, setGoal] = useState('');
  const [requiredCapabilities, setRequiredCapabilities] = useState('coding, graph-analysis');
  const [privacyRequirement, setPrivacyRequirement] = useState<PrivacyRequirement>('any');
  const [inputTokens, setInputTokens] = useState('12000');
  const [outputTokens, setOutputTokens] = useState('3000');
  const [cacheReadTokens, setCacheReadTokens] = useState('0');
  const [cacheWriteTokens, setCacheWriteTokens] = useState('0');
  const [agents, setAgents] = useState('3');
  const [retries, setRetries] = useState('0');
  const [successRatePercent, setSuccessRatePercent] = useState('85');
  const [plannedRunsPerMonth, setPlannedRunsPerMonth] = useState('100');
  const [perRunBudget, setPerRunBudget] = useState('');
  const [monthlyBudget, setMonthlyBudget] = useState('');
  const [subscriptionMonthly, setSubscriptionMonthly] = useState('');
  const [subscriptionAllocation, setSubscriptionAllocation] = useState('100');
  const [otherFixed, setOtherFixed] = useState('0');
  const [gpuRate, setGpuRate] = useState('');
  const [gpuHours, setGpuHours] = useState('');
  const [gpuUtilization, setGpuUtilization] = useState('');
  const [costWeight, setCostWeight] = useState('0.6');
  const [qualityWeight, setQualityWeight] = useState('0.3');
  const [latencyWeight, setLatencyWeight] = useState('0.1');
  const [candidates, setCandidates] = useState<Candidate[]>(() => starters);
  const [exportMessage, setExportMessage] = useState('');
  const [search, setSearch] = useState('');
  const [harnessFilter, setHarnessFilter] = useState('all');
  const [providerFilter, setProviderFilter] = useState('all');
  const [readinessFilter, setReadinessFilter] = useState('all');
  const [openCandidateId, setOpenCandidateId] = useState<string | null>(null);

  const request = useMemo(() => ({
    taskClass, goal, requiredCapabilities: requiredCapabilities.split(',').map(item => item.trim()).filter(Boolean), privacyRequirement,
    inputTokens: Number(inputTokens), outputTokens: Number(outputTokens), cacheReadTokens: Number(cacheReadTokens), cacheWriteTokens: Number(cacheWriteTokens),
    agents: Number(agents), retries: Number(retries), successRatePercent: Number(successRatePercent), plannedRunsPerMonth: Number(plannedRunsPerMonth),
    monthlyBudgetUsd: numberOrNull(monthlyBudget), perRunBudgetUsd: numberOrNull(perRunBudget),
    allocatedSubscriptionMonthlyUsd: numberOrNull(subscriptionMonthly) ?? 0, subscriptionAllocationPercent: Number(subscriptionAllocation),
    otherFixedMonthlyUsd: Number(otherFixed), gpuRateUsdPerGpuHour: numberOrNull(gpuRate), gpuHoursPerAttempt: numberOrNull(gpuHours), gpuUtilizationPercent: numberOrNull(gpuUtilization),
    weights: { cost: Number(costWeight), quality: Number(qualityWeight), latency: Number(latencyWeight) },
  }), [taskClass, goal, requiredCapabilities, privacyRequirement, inputTokens, outputTokens, cacheReadTokens, cacheWriteTokens, agents, retries, successRatePercent, plannedRunsPerMonth, monthlyBudget, perRunBudget, subscriptionMonthly, subscriptionAllocation, otherFixed, gpuRate, gpuHours, gpuUtilization, costWeight, qualityWeight, latencyWeight]);
  const completePlan = useMemo(() => buildDelegationPlan({ request, candidates }), [request, candidates]);
  const readyById = new Map(completePlan.candidates.map(item => [item.candidate.id, item]));
  const visibleCandidates = candidates.filter(candidate => {
    const query = search.trim().toLowerCase();
    if (query && !`${candidate.name} ${candidate.modelId} ${candidate.harnessId} ${candidate.provider}`.toLowerCase().includes(query)) return false;
    if (harnessFilter !== 'all' && candidate.harnessId !== harnessFilter) return false;
    if (providerFilter !== 'all' && candidate.provider !== providerFilter) return false;
    const assessment = readyById.get(candidate.id);
    if (readinessFilter === 'rankable' && assessment?.rankScore === null) return false;
    if (readinessFilter === 'needs-evidence' && (assessment?.rankScore !== null || assessment?.eligible === false)) return false;
    if (readinessFilter === 'blocked' && assessment?.eligible !== false) return false;
    return true;
  });
  const plan = useMemo(() => buildDelegationPlan({ request, candidates: visibleCandidates }), [request, visibleCandidates]);
  const assessment = new Map(plan.candidates.map(item => [item.candidate.id, item]));

  function update(id: string, change: (candidate: Candidate) => Candidate) {
    setCandidates(previous => previous.map(candidate => candidate.id === id ? change(candidate) : candidate));
  }
  function addCustomCandidate() {
    const id = `custom-${Date.now()}`;
    setCandidates(previous => [...previous, { id, name: 'Custom model route', harnessId: 'opencode', provider: 'manual', modelId: '', capabilities: [], privacy: 'unknown', rates: { inputPerMillionUsd: null, outputPerMillionUsd: null, cacheReadPerMillionUsd: null, cacheWritePerMillionUsd: null }, ratesCheckedAt: '', rateSource: '', qualityScore: null, qualityBenchmark: '', benchmarkDate: '', benchmarkSamples: null, p95LatencyMs: null, maxContextTokens: null, maxOutputTokens: null, enabled: true }]);
    setOpenCandidateId(id);
  }
  function exportPlan() {
    const blob = new Blob([JSON.stringify(plan, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a'); link.href = url; link.download = 'apexgraphswarm-delegation-plan.json'; link.click(); URL.revokeObjectURL(url);
    setExportMessage('Plan exported. It contains assumptions and no credentials; it does not start an execution.');
  }
  const field = (label: string, value: string, set: (value: string) => void, attrs: { min?: number; max?: number; step?: number; placeholder?: string; help?: string } = {}) => <label className="economics-field" key={label}><span>{label}</span><input type="number" min={attrs.min ?? 0} max={attrs.max} step={attrs.step ?? 'any'} value={value} placeholder={attrs.placeholder} onChange={event => set(event.target.value)} />{attrs.help && <small>{attrs.help}</small>}</label>;

  return <section className="execution-economics delegation-planner" aria-labelledby="delegation-planner-title">
    <header className="economics-heading"><div><span className="eyebrow">PLANNING · NO PROVIDER CALLS</span><h2 id="delegation-planner-title">Delegation planner</h2><p>Compare eligible routes against this task’s requirements and your dated benchmark evidence. Planning and JSON export do not dispatch work.</p></div></header>
    <div className={styles.taskGrid}>
      <fieldset><legend>Task and constraints</legend>
        <label className="economics-field"><span>Task class</span><input value={taskClass} maxLength={80} onChange={event => setTaskClass(event.target.value)} /></label>
        <label className="economics-field"><span>Goal</span><textarea rows={3} maxLength={2000} value={goal} onChange={event => setGoal(event.target.value)} /></label>
        <label className="economics-field"><span>Required capabilities</span><input value={requiredCapabilities} onChange={event => setRequiredCapabilities(event.target.value)} /><small>Comma-separated; candidate capability tags must match.</small></label>
        <label className="economics-field"><span>Privacy requirement</span><select value={privacyRequirement} onChange={event => setPrivacyRequirement(event.target.value as PrivacyRequirement)}><option value="any">No additional filter</option><option value="no-training">Verified no-training or local route</option><option value="local-only">Local execution only</option></select></label>
      </fieldset>
      <fieldset><legend>Workload and budgets</legend>
        {field('Uncached input tokens / agent attempt', inputTokens, setInputTokens)}{field('Output tokens / attempt', outputTokens, setOutputTokens)}{field('Cache-read tokens / attempt', cacheReadTokens, setCacheReadTokens)}{field('Cache-write tokens / attempt', cacheWriteTokens, setCacheWriteTokens)}
        {field('Agents / run', agents, setAgents, { min: 1, step: 1 })}{field('Retries / agent', retries, setRetries, { step: 1 })}{field('Expected success rate (%)', successRatePercent, setSuccessRatePercent, { max: 100 })}{field('Started runs / month', plannedRunsPerMonth, setPlannedRunsPerMonth, { step: 1 })}
        {field('Budget / started run (USD)', perRunBudget, setPerRunBudget, { placeholder: 'Optional' })}{field('Monthly budget (USD)', monthlyBudget, setMonthlyBudget, { placeholder: 'Optional' })}
      </fieldset>
      <fieldset><legend>Fixed and hosting allocation</legend>{field('Subscription cost / month (USD)', subscriptionMonthly, setSubscriptionMonthly, { placeholder: 'Unknown until entered' })}{field('Subscription allocation (%)', subscriptionAllocation, setSubscriptionAllocation, { max: 100 })}{field('Other fixed cost / month (USD)', otherFixed, setOtherFixed)}
        <p className="economics-notice">Subscriptions are fixed plan allocations, not unlimited API tokens. vLLM estimates use separate GPU hosting inputs. Unknown remains unknown.</p>
        {field('vLLM GPU rate (USD/GPU-hour)', gpuRate, setGpuRate, { placeholder: 'Optional' })}{field('GPU wall hours / attempt', gpuHours, setGpuHours, { placeholder: 'Optional' })}{field('GPU utilization (%)', gpuUtilization, setGpuUtilization, { max: 100, placeholder: 'Optional' })}
      </fieldset>
      <fieldset><legend>Ranking weights</legend>{field('Cost weight', costWeight, setCostWeight, { max: 1, step: 0.05 })}{field('Benchmark quality weight', qualityWeight, setQualityWeight, { max: 1, step: 0.05 })}{field('p95 latency weight', latencyWeight, setLatencyWeight, { max: 1, step: 0.05 })}<p className="help-text">Weights are normalized during scoring. Enter a dated benchmark and measured latency on candidate cards; no score is inferred from provider/model names.</p></fieldset>
    </div>
    <div className="section-title-row"><h3>Candidate registry</h3><button type="button" className="secondary-button" onClick={addCustomCandidate}>Add custom model/API route</button></div>
    <p className="help-text">Rates, capabilities, limits and benchmark fields are editable planning records. Built-in GPT-6/GPT-5.6/GPT-5.5/Daybreak entries have unknown pricing unless you enter a verified route. A prefilled OpenRouter rate is a dated reference, not a live quote.</p>
    <div className={styles.registryToolbar}>
      <label><span>Search candidates</span><input type="search" value={search} onChange={event => setSearch(event.target.value)} placeholder="Model, API ID, harness, provider" /></label>
      <label><span>Harness</span><select value={harnessFilter} onChange={event => setHarnessFilter(event.target.value)}><option value="all">All harnesses</option>{harnessCatalog.map(harness => <option key={harness.id} value={harness.id}>{harness.name}</option>)}</select></label>
      <label><span>Provider mode</span><select value={providerFilter} onChange={event => setProviderFilter(event.target.value)}><option value="all">All provider modes</option>{(['gateway', 'openrouter', 'vllm', 'subscription', 'manual'] as ProviderMode[]).map(mode => <option key={mode} value={mode}>{mode}</option>)}</select></label>
      <label><span>Readiness</span><select value={readinessFilter} onChange={event => setReadinessFilter(event.target.value)}><option value="all">All</option><option value="rankable">Rankable</option><option value="needs-evidence">Needs evidence</option><option value="blocked">Blocked by constraints</option></select></label>
    </div>
    <p className="help-text" aria-live="polite">Showing {visibleCandidates.length} of {candidates.length} candidates. Search and filters scope this comparison and its exported plan.</p>
    <div className={styles.registryList}>
      {visibleCandidates.map(candidate => {
        const result = assessment.get(candidate.id) ?? readyById.get(candidate.id)!;
        const harnessName = harnessCatalog.find(harness => harness.id === candidate.harnessId)?.name ?? candidate.harnessId;
        const set = (change: Partial<Candidate>) => update(candidate.id, current => ({ ...current, ...change }));
        const rate = (key: keyof Candidate['rates']) => (value: string) => update(candidate.id, current => candidateWithRate(current, key, numberOrNull(value)));
        const readiness = result.rankScore !== null ? `Ranked · ${result.rankScore.toFixed(3)}` : result.eligible ? 'Needs evidence' : 'Blocked';
        return <details key={candidate.id} className={styles.candidateDisclosure} open={openCandidateId === candidate.id} onToggle={event => {
          const isOpen = event.currentTarget.open;
          setOpenCandidateId(current => isOpen ? candidate.id : current === candidate.id ? null : current);
        }}>
          <summary className={styles.candidateSummary}>
            <span className={styles.candidateIdentity}><strong>{candidate.name || 'Unnamed route'}</strong><small>{candidate.modelId || 'Model/API ID not entered'} · {harnessName}</small></span>
            <span className={styles.candidateRoute}><strong>{candidate.provider}</strong><small>{candidate.ratesCheckedAt ? `Rates checked ${candidate.ratesCheckedAt}` : 'Rate date unknown'}</small></span>
            <span><strong>{money(result.estimate?.costPerSuccessfulRunUsd)}</strong><small>Estimated cost / success</small></span>
            <span className={styles.readinessBadge} data-state={result.rankScore !== null ? 'ready' : result.eligible ? 'evidence' : 'blocked'}>{readiness}</span>
          </summary>
          <fieldset className={styles.candidateEditor}><legend className={styles.srOnly}>Edit {candidate.name || 'candidate'} details</legend>
          <div className={styles.editorGrid}>
          <label className="economics-field"><span>Candidate name</span><input value={candidate.name} onChange={event => set({ name: event.target.value })} /></label>
          <label className="economics-field"><span>Harness</span><select value={candidate.harnessId} onChange={event => set({ harnessId: event.target.value as HarnessId })}>{harnessCatalog.map(harness => <option key={harness.id} value={harness.id}>{harness.name}</option>)}</select></label>
          <label className="economics-field"><span>Billing/provider mode</span><select value={candidate.provider} onChange={event => set({ provider: event.target.value as ProviderMode })}>{(['gateway', 'openrouter', 'vllm', 'subscription', 'manual'] as ProviderMode[]).map(mode => <option key={mode} value={mode}>{mode}</option>)}</select></label>
          <label className="economics-field"><span>Model or API ID</span><input value={candidate.modelId} onChange={event => set({ modelId: event.target.value })} placeholder="Exact ID from your configured route" /></label>
          <label className="economics-field"><span>Capabilities (comma-separated)</span><input value={candidate.capabilities.join(', ')} onChange={event => set({ capabilities: event.target.value.split(',').map(value => value.trim()).filter(Boolean) })} placeholder="coding, graph-analysis" /></label>
          <label className="economics-field"><span>Privacy evidence</span><select value={candidate.privacy} onChange={event => set({ privacy: event.target.value as Candidate['privacy'] })}><option value="unknown">Unknown</option><option value="provider-policy">Provider policy (standard)</option><option value="no-training">No-training verified</option><option value="local-only">Local-only verified</option></select></label>
          <label className="economics-field"><span>Rate checked date</span><input type="date" value={candidate.ratesCheckedAt} onChange={event => set({ ratesCheckedAt: event.target.value })} /></label>
          <label className="economics-field"><span>Rate source URL</span><input value={candidate.rateSource} onChange={event => set({ rateSource: event.target.value })} placeholder="Official pricing/catalog source" /></label>
          {([['inputPerMillionUsd', 'Input USD / 1M'], ['outputPerMillionUsd', 'Output USD / 1M'], ['cacheReadPerMillionUsd', 'Cache-read USD / 1M'], ['cacheWritePerMillionUsd', 'Cache-write USD / 1M']] as const).map(([key, label]) => <label className="economics-field" key={key}><span>{label}</span><input type="number" min="0" step="any" value={valueOrEmpty(candidate.rates[key])} placeholder="Unknown" onChange={event => rate(key)(event.target.value)} /></label>)}
          <label className="economics-field"><span>Benchmark score (0–100)</span><input type="number" min="0" max="100" value={valueOrEmpty(candidate.qualityScore)} onChange={event => set({ qualityScore: numberOrNull(event.target.value) })} /></label>
          <label className="economics-field"><span>Benchmark name / dataset</span><input value={candidate.qualityBenchmark} onChange={event => set({ qualityBenchmark: event.target.value })} /></label>
          <label className="economics-field"><span>Benchmark date</span><input type="date" value={candidate.benchmarkDate} onChange={event => set({ benchmarkDate: event.target.value })} /></label>
          {field(`Benchmark sample count · ${candidate.id}`, valueOrEmpty(candidate.benchmarkSamples), value => set({ benchmarkSamples: numberOrNull(value) }), { step: 1 })}
          {field(`Measured p95 latency ms · ${candidate.id}`, valueOrEmpty(candidate.p95LatencyMs), value => set({ p95LatencyMs: numberOrNull(value) }), { step: 1 })}
          {field(`Context limit tokens · ${candidate.id}`, valueOrEmpty(candidate.maxContextTokens), value => set({ maxContextTokens: numberOrNull(value) }), { step: 1 })}
          {field(`Output limit tokens · ${candidate.id}`, valueOrEmpty(candidate.maxOutputTokens), value => set({ maxOutputTokens: numberOrNull(value) }), { step: 1 })}
          <label className="economics-field"><span><input type="checkbox" checked={candidate.enabled} onChange={event => set({ enabled: event.target.checked })} /> Eligible for comparison</span></label>
          </div>
          <div className="economics-results"><div><span>Assessment</span><strong>{result.eligible ? 'Eligible' : 'Blocked'}</strong></div><div><span>Cost / success</span><strong>{money(result.estimate?.costPerSuccessfulRunUsd)}</strong></div><div><span>Budget</span><strong>{result.estimate?.perRunBudgetStatus ?? 'Unknown'} / {result.estimate?.monthlyBudgetStatus ?? 'Unknown'}</strong></div></div>
          {result.blockers.length > 0 && <p className="economics-notice">{result.blockers.join(' ')}</p>}
          {result.rankExplanation && <p className="help-text">{result.rankExplanation}</p>}
          {candidate.ratesCheckedAt && <p className="help-text">Rate source checked {candidate.ratesCheckedAt}: <code>{candidate.rateSource || 'source URL missing'}</code></p>}
          <button type="button" className="text-button" onClick={() => setCandidates(previous => previous.filter(item => item.id !== candidate.id))}>Remove candidate</button>
          </fieldset>
        </details>;
      })}
      {visibleCandidates.length === 0 && <p className="economics-notice">No candidates match these filters. Change a filter or search term to continue.</p>}
    </div>
    <div className="economics-notice" aria-live="polite"><strong>Plan result:</strong> {plan.recommendation}{plan.recommendedCandidateId && <p>Selected candidate: {plan.candidates.find(item => item.candidate.id === plan.recommendedCandidateId)?.candidate.name}</p>}</div>
    <div className="button-row"><button type="button" className="primary-button" onClick={exportPlan}>Export JSON plan</button></div>{exportMessage && <p role="status" className="help-text">{exportMessage}</p>}
    <p className="economics-footnote">This plan is not an execution, reservation, invoice, or entitlement. Estimates reuse the execution-economics formulas and may remain unknown when prices, success rates, subscription consumption, or hosting allocation are missing. No provider calls or secret handling occur here.</p>
  </section>;
}
