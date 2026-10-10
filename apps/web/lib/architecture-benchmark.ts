/**
 * Constant workloadProfiles.
 *
 *
 * @example
 * ```typescript
 * import { workloadProfiles } from './module';
 * ```
 */
export const workloadProfiles = [
/**
 * Core library module for architecture benchmark.ts functionality.
 *
 * @module architecture-benchmark
 * @packageDocumentation
 */
  {id:'repository-change',name:'Repository engineering',baseline:'One agent, the same model/tools, lexical repository search, no delegation.',metrics:['Held-out task success with executable acceptance tests','Wall-clock p50/p95/p99, including queue wait','Actual model/tool/compute USD per accepted change','Duplicate side effects and conflict/rework rate','Tokens and tool calls per attempt, including failed attempts']},
  {id:'multi-hop-retrieval',name:'GraphRAG & retrieval',baseline:'Lexical retrieval and vector-only retrieval on the same corpus snapshot; graph expansion disabled.',metrics:['Recall@10 and nDCG@10 against held-out relevance labels','Answer correctness and citation support under the same generation model','Filtered query p50/p95/p99 at matched recall and concurrency','Ingest/index/update time, peak RAM and index size','USD per verified answer, including amortized ingest and reindexing']},
  {id:'long-running-operations',name:'Durable agent operations',baseline:'One durable worker with the same task DAG, failure schedule and tool permissions.',metrics:['Completion rate under injected timeout/restart failures','Queue wait, lease recovery and resume p50/p95/p99','Duplicate external side effects and unresolved usage receipts','Budget overshoot, throttle rate and cancellation latency','Actual USD per successful operation, including idle capacity']},
] as const;
/**
 * Type WorkloadId.
 *
 *
 * @example
 * ```typescript
 * import { WorkloadId } from './module';
 * ```
 */
export type WorkloadId = typeof workloadProfiles[number]['id'];
/**
 * Type BenchmarkDraft.
 *
 *
 * @example
 * ```typescript
 * import { BenchmarkDraft } from './module';
 * ```
 */
export type BenchmarkDraft = {workload:WorkloadId;candidateIds:string[];modelRevision:string;datasetRevision:string;environment:string;priceEvidence:string;componentPins:string;trials:number;taskCount:number;activeWorkers:number;budgetUsd:number|null;minimumSuccessRate:number|null;maxP95Seconds:number|null;maxUsdPerSuccess:number|null};
const fields = ['modelRevision','datasetRevision','environment','priceEvidence','componentPins'] as const;
/**
 * Function createArchitectureBenchmark.
 *
 * @param {BenchmarkDraft} input - Description of input.
 * @param {readonly string[]} allowedIds - Description of allowedIds.
 *
 * @example
 * ```typescript
 * const result = createArchitectureBenchmark(..., ...);
 * ```
 */
export function createArchitectureBenchmark(input:BenchmarkDraft, allowedIds:readonly string[]) {
 const profile=workloadProfiles.find(item=>item.id===input.workload);
 if(!profile)throw new Error('Choose a known workload.');
 if(!Array.isArray(input.candidateIds)||input.candidateIds.length>24||new Set(input.candidateIds).size!==input.candidateIds.length||input.candidateIds.some(id=>!allowedIds.includes(id)))throw new Error('Candidates must be unique catalog entries (maximum 24).');
 for(const [key,max] of [['trials',100],['taskCount',10000],['activeWorkers',64]] as const){if(!Number.isSafeInteger(input[key])||input[key]<1||input[key]>max)throw new Error(`${key} must be an integer from 1 to ${max}.`);}
 if(input.budgetUsd!==null&&(!Number.isFinite(input.budgetUsd)||input.budgetUsd<=0||input.budgetUsd>1e6))throw new Error('Use a positive scenario budget up to USD 1,000,000, or leave it unknown.');
 for(const key of fields)if(typeof input[key]!=='string'||input[key].length>4000)throw new Error(`${key} must contain at most 4,000 characters.`);
 for(const [key,max] of [['minimumSuccessRate',1],['maxP95Seconds',86400],['maxUsdPerSuccess',1e6]] as const){const value=input[key];if(value!==null&&(!Number.isFinite(value)||value<=0||value>max))throw new Error(`${key} must be greater than zero and at most ${max}, or unknown.`);}
 const missing:string[]=fields.filter(key=>!input[key].trim());
 if(!input.candidateIds.length)missing.push('candidateIds');
 if(input.budgetUsd===null)missing.push('budgetUsd');
 for(const key of ['minimumSuccessRate','maxP95Seconds','maxUsdPerSuccess'] as const)if(input[key]===null)missing.push(key);
 return {
  schemaVersion:1,classification:'planning-only',executionEnabled:false,
  designComplete:missing.length===0,missingEvidence:missing,
  workload:profile.id,baseline:profile.baseline,candidateIds:[...input.candidateIds],
  pins:Object.fromEntries(fields.map(key=>[key,input[key].trim()||null])),
  workloadSize:{heldOutTasks:input.taskCount,independentTrials:input.trials,activeWorkers:input.activeWorkers},
  budget:{currency:'USD',scenarioCap:input.budgetUsd,liveAdmissionConfigured:false},
  thresholds:{minimumVerifiedSuccessRate:input.minimumSuccessRate,maxEndToEndP95Seconds:input.maxP95Seconds,maxUsdPerSuccessfulResult:input.maxUsdPerSuccess},
  metrics:[...profile.metrics],
  protocol:['Pin code/images, model/provider, corpus and evaluation data before running.','Use identical task samples, tool permissions, token ceilings and timeout policies across candidates.','Change one architecture factor at a time; record any irreducible configuration differences.','Separate cold ingest, warm query, model latency, queue delay and framework overhead.','Run paired independent trials; retain raw traces, failures, usage receipts and confidence intervals.','Test restart, cancellation, throttling and partial side effects under bounded concurrency.','Compare quality/cost/latency tradeoffs; do not rank unmatched publisher results as a universal leaderboard.'],
  acceptanceGates:['Held-out task quality meets the declared workload threshold.','No duplicate external side effects in the tested recovery scenarios.','Cost reconciles with provider/tool receipts and includes failures/retries.','Promotion requires reviewed evidence and separately configured execution adapters.'],
 };
}
