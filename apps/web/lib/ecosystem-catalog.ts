/**
 * Type EcosystemLayer.
 *
 *
 * @example
 * ```typescript
 * import { EcosystemLayer } from './module';
 * ```
 */
export type EcosystemLayer = 'executor' | 'gateway' | 'registry' | 'skills';
/**
 * Constant ecosystemCatalog.
 *
 *
 * @example
 * ```typescript
 * import { ecosystemCatalog } from './module';
 * ```
 */
export const ecosystemCatalog = [
/**
 * Core library module for ecosystem catalog.ts functionality.
 *
 * @module ecosystem-catalog
 * @packageDocumentation
 */
  {id:'google-ax', name:'Google AX', layer:'executor', status:'Architecture assessed · adapter planned', source:'https://github.com/google/ax', description:'Declarative Task, Workspace and Model orchestration over Agent Substrate. Requires a separate cluster and lifecycle/accounting adapter.', limits:'No AX deployment or 150K-agent benchmark is included. Keep logical agents, active sandboxes and simultaneous model calls separate.'},
  {id:'agentgateway', name:'agentgateway', layer:'gateway', status:'Bring your configured endpoint', source:'https://github.com/agentgateway/agentgateway', description:'Agent and MCP proxy candidate. Connect a compatible, administrator-configured MCP HTTP endpoint through discovery below.', limits:'Authentication, routing policy, quotas, tool identity and protocol compatibility require deployment-specific verification.'},
  {id:'docker-mcp', name:'Docker MCP Gateway', layer:'gateway', status:'Bring your configured endpoint', source:'https://github.com/docker/mcp-gateway', description:'Container-based MCP gateway candidate. Operate it independently and expose an explicitly configured compatible HTTP endpoint.', limits:'A local stdio gateway needs a separate bridge. Apex does not launch containers or import its full catalog automatically.'},
  {id:'mcp-registry', name:'Official MCP Registry', layer:'registry', status:'Discovery source · external', source:'https://registry.modelcontextprotocol.io', description:'Find server metadata and deployment references, then review and configure the endpoint in Apex.', limits:'A registry listing is neither a safety endorsement nor evidence that a server is reachable or compatible.'},
  {id:'skills-sh', name:'skills.sh', layer:'skills', status:'Review import available', source:'https://skills.sh/docs', description:'Discover reusable agent skills. Paste the selected SKILL.md below with its source and pinned revision for a local review manifest.', limits:'No package installation, remote fetching or script execution. Companion files and harness support require separate review.'},
  {id:'agent-skills', name:'Agent Skills specification', layer:'skills', status:'Bounded SKILL.md review', source:'https://agentskills.io/specification', description:'Portable skill format for instructions and supporting resources. Review content and declared requirements before enabling it in a harness.', limits:'The local parser supports an explicit subset of YAML. A valid content hash establishes identity, not safety or compatibility.'},
] as const;
/**
 * Type EcosystemId.
 *
 *
 * @example
 * ```typescript
 * import { EcosystemId } from './module';
 * ```
 */
export type EcosystemId = typeof ecosystemCatalog[number]['id'];
/**
 * Constant costLines.
 *
 *
 * @example
 * ```typescript
 * import { costLines } from './module';
 * ```
 */
export const costLines = [
  ['model','Model usage','million weighted tokens'],
  ['active','Active sandbox compute','sandbox-hours'],
  ['suspended','Suspended state storage','GB-months'],
  ['gateway','MCP gateway/tool fees','calls'],
  ['resume','Resume operations','resumes'],
  ['egress','Network egress','GB'],
  ['platform','Cluster / observability / subscription allocation','allocated units'],
  ['embedding','Embedding ingestion and refresh','million tokens'],
  ['reranking','Reranker service','requests'],
  ['indexStorage','Graph/vector index storage','GB-months'],
  ['retrieval','Managed retrieval/query fees','requests'],
  ['indexBuild','Graph extraction / index compute','compute-hours'],
] as const;
/**
 * Type CostId.
 *
 *
 * @example
 * ```typescript
 * import { CostId } from './module';
 * ```
 */
export type CostId = typeof costLines[number][0];
/**
 * Type CostAssumption.
 *
 *
 * @example
 * ```typescript
 * import { CostAssumption } from './module';
 * ```
 */
export type CostAssumption = {id:CostId; quantity:number|null; usdPerUnit:number|null};
/**
 * Function estimateEcosystemCost.
 *
 * @param {CostAssumption[]} items - Description of items.
 * @param {number|null} successes - Description of successes.
 *
 * @example
 * ```typescript
 * const result = estimateEcosystemCost(..., ...);
 * ```
 */
export function estimateEcosystemCost(items:CostAssumption[], successes:number|null) {
  const seen = new Set<string>(); let knownSubtotalUsd = 0;
  for (const item of items) {
    if (!costLines.some(([id])=>id===item.id) || seen.has(item.id)) throw new Error('Cost categories must be known and unique.');
    seen.add(item.id);
    for (const value of [item.quantity,item.usdPerUnit]) if(value!==null && (!Number.isFinite(value)||value<0)) throw new Error('Use finite, nonnegative assumptions.');
    if(item.quantity!==null&&item.usdPerUnit!==null) knownSubtotalUsd+=item.quantity*item.usdPerUnit;
  }
  if(!Number.isFinite(knownSubtotalUsd)) throw new Error('Cost exceeds the supported numeric range.');
  if(successes!==null&&(!Number.isSafeInteger(successes)||successes<0)) throw new Error('Successful results must be a nonnegative integer.');
  const missing = costLines.filter(([id])=>!items.some(item=>item.id===id&&item.quantity!==null&&item.usdPerUnit!==null)).map(([id])=>id);
  const complete = missing.length===0;
  return {knownSubtotalUsd,complete,missing,totalUsd:complete?knownSubtotalUsd:null,costPerSuccessUsd:complete&&successes!==null&&successes>0?knownSubtotalUsd/successes:null};
}
