/**
 * React component for ecosystem workspace.
 *
 * @module EcosystemWorkspace
 * @packageDocumentation
 */
'use client';
import {useState} from 'react';
import Link from 'next/link';
import {ArrowUpRight,Download,Search,Plug,ShieldCheck,Layers} from 'lucide-react';
import {costLines,ecosystemCatalog,estimateEcosystemCost,type CostAssumption,type EcosystemId} from '@/lib/ecosystem-catalog';
import {reviewSkillImport,type SkillImportReview} from '@/lib/skill-manifest';
import styles from './EcosystemWorkspace.module.css';

/**
 * Type Server.
 *
 *
 * @example
 * ```typescript
 * import { Server } from './module';
 * ```
 */
type Server = {id:string;label:string;configured:boolean;statusText:string};
/**
 * Type Discovery.
 *
 *
 * @example
 * ```typescript
 * import { Discovery } from './module';
 * ```
 */
type Discovery = {server:{id:string;label:string;protocolVersion:string};tools:Array<{name:string;description?:string;inputSchema?:unknown;annotations?:unknown}>;pagination:{pages:number;truncated:boolean}};
/**
 * Function download.
 *
 * @param {string} name - Description of name.
 * @param data - Description of data.
 *
 * @example
 * ```typescript
 * const result = download(..., ...);
 * ```
 */
function download(name:string,data:unknown){const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
/**
 * Function numberOrNull.
 *
 * @param {string} text - Description of text.
 *
 * @example
 * ```typescript
 * const result = numberOrNull(...);
 * ```
 */
function numberOrNull(text:string){return text.trim()===''?null:Number(text);}

/**
 * React component EcosystemWorkspace.
 *
 *
 * @example
 * ```typescript
 * import { EcosystemWorkspace } from './module';
 * ```
 */
export default function EcosystemWorkspace(){
 const [query,setQuery]=useState('');const [layer,setLayer]=useState('all');
 const [selected,setSelected]=useState<EcosystemId[]>(['google-ax','skills-sh']);
 const [token,setToken]=useState('');const [servers,setServers]=useState<Server[]>([]);const [loaded,setLoaded]=useState(false);const [serverId,setServerId]=useState('');
 const [busy,setBusy]=useState(false);const [message,setMessage]=useState('');const [discovery,setDiscovery]=useState<Discovery|null>(null);const [toolQuery,setToolQuery]=useState('');
 const [skillText,setSkillText]=useState('');const [sourceUrl,setSourceUrl]=useState('');const [revision,setRevision]=useState('');const [review,setReview]=useState<SkillImportReview|null>(null);const [reviewing,setReviewing]=useState(false);
 const [costs,setCosts]=useState<CostAssumption[]>(costLines.map(([id])=>({id,quantity:null,usdPerUnit:null})));const [successes,setSuccesses]=useState('');const [rateSource,setRateSource]=useState('');const [rateDate,setRateDate]=useState('');
 let estimate:ReturnType<typeof estimateEcosystemCost>|null=null;let costError='';try{estimate=estimateEcosystemCost(costs,numberOrNull(successes));}catch(error){costError=error instanceof Error?error.message:'Invalid assumptions';}
 const filtered=ecosystemCatalog.filter(item=>(layer==='all'||item.layer===layer)&&`${item.name} ${item.description}`.toLowerCase().includes(query.toLowerCase()));
 async function loadServers(){setBusy(true);setMessage('');setDiscovery(null);try{const response=await fetch('/api/ecosystem/mcp',{cache:'no-store'});const data=await response.json();if(!response.ok)throw new Error(data.error||'Could not load configured endpoints');if(data.configurationError){setServers([]);setLoaded(false);throw new Error(data.configurationError);}setServers(data.servers);setLoaded(true);setServerId(data.servers.find((s:Server)=>s.configured)?.id||'');}catch(error){setMessage(error instanceof Error?error.message:'Request failed');}finally{setBusy(false);}}
 async function discover(){setBusy(true);setMessage('');setDiscovery(null);try{const response=await fetch('/api/ecosystem/mcp',{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`},body:JSON.stringify({serverId})});const data=await response.json();if(!response.ok)throw new Error(data.error||'Discovery failed');setDiscovery(data);setMessage('Discovery complete. Tools remain unapproved for execution.');}catch(error){setMessage(error instanceof Error?error.message:'Discovery failed');}finally{setBusy(false);}}
 async function reviewSkill(){setReviewing(true);try{setReview(await reviewSkillImport({skillText,sourceUrl,exactRevision:revision}));}catch{setReview({status:'invalid',valid:false,manifest:null,errors:['Could not review this skill.'],warnings:[]});}finally{setReviewing(false);}}
 function exportPlan(){download('apex-ecosystem-plan.json',{schemaVersion:1,classification:'planning-only',createdAt:new Date().toISOString(),components:ecosystemCatalog.filter(item=>selected.includes(item.id)),mcp:discovery?{serverId:discovery.server.id,protocolVersion:discovery.server.protocolVersion,discoveredToolNames:discovery.tools.map(tool=>tool.name),truncated:discovery.pagination.truncated,executionApproved:false}:null,skill:review?.manifest??null,costs:{currency:'USD',assumptions:costs,expectedSuccessfulResults:numberOrNull(successes),rateEvidence:{source:rateSource||null,asOf:rateDate||null,status:'user-entered-unverified'},estimate},constraints:{axAdapter:'planned',scale:'150K+ agents unverified for this deployment',toolsExecutable:false,skillInstallation:false,credentialsIncluded:false}});}
 return <>
  <div className="apex-actions" style={{marginBottom:20}}><Link className="primary-button" href="/ecosystem/research">Compare orchestration, GraphRAG & bottlenecks →</Link></div>
  <nav className={styles.jumpLinks} aria-label="Ecosystem sections"><a href="#connections">Connections</a><a href="#mcp">MCP discovery</a><a href="#skills">Skill review</a><a href="#costs">Operating costs</a></nav>
  <div className={styles.architecture} aria-label="Integration architecture"><div><Layers size={20}/><strong>Apex control plane</strong><span>Policy · budgets · evaluation</span></div><span aria-hidden="true">→</span><div><Plug size={20}/><strong>Execution adapters</strong><span>Local fixtures now · AX planned</span></div><span aria-hidden="true">→</span><div><ShieldCheck size={20}/><strong>Tools & skills</strong><span>Discover · review · pin</span></div></div>
  <section id="connections" className="apex-panel"><div className="apex-panel-heading"><div><h2>Choose the building blocks</h2><p>Selections form a reviewable architecture plan. They do not install or activate services.</p></div><span className="pill">{selected.length} selected</span></div>
   <div className={styles.filters}><label><Search size={14}/> Find a connection<input value={query} onChange={e=>setQuery(e.target.value)} placeholder="AX, gateway, skills…"/></label><label>Layer<select value={layer} onChange={e=>setLayer(e.target.value)}><option value="all">All layers</option><option value="executor">Executors</option><option value="gateway">Gateways</option><option value="registry">Registries</option><option value="skills">Skills libraries</option></select></label></div>
   <div className={styles.cards}>{filtered.map(item=><article key={item.id} className={styles.card}><div className={styles.cardTitle}><label><input type="checkbox" checked={selected.includes(item.id)} onChange={e=>setSelected(current=>e.target.checked?[...current,item.id]:current.filter(id=>id!==item.id))}/><strong>{item.name}</strong></label><span>{item.layer}</span></div><small>{item.status}</small><p>{item.description}</p><details><summary>Requirements & limitations</summary><p>{item.limits}</p></details><a href={item.source} target="_blank" rel="noreferrer">Official source <ArrowUpRight size={13}/></a></article>)}</div>{filtered.length===0&&<p className="apex-note">No matching connections.</p>}
   <p className="apex-note">Google AX is a candidate distributed executor. Its upstream scale ambitions are not a measured Apex capacity. Validate queue delay, active sandbox capacity, resume latency, recovery, model quotas and cost per successful task before increasing admission limits. <Link href="/evaluations">Open Evaluation lab →</Link></p>
  </section>
  <section id="mcp" className="apex-panel"><div className="apex-panel-heading"><div><h2>Inspect configured MCP servers</h2><p>Read-only discovery through server-owned endpoints. Tools are displayed as untrusted metadata.</p></div><span className="pill">No tool execution</span></div>
   <div className="apex-actions"><button className="secondary-button" disabled={busy} onClick={loadServers}>{busy?'Working…':'Load configured endpoints'}</button></div>
   {loaded&&servers.length===0&&<div className={styles.empty}><Plug size={22}/><div><strong>No MCP endpoints configured</strong><p>Set MCP_SERVERS_JSON in the server environment using the .env.example contract, then restart the web server. Configure a direct server or gateway endpoint; credentials stay in server environment variables.</p></div></div>}
   {servers.length>0&&<><div className="apex-form-grid"><label>Server or gateway<select disabled={busy} value={serverId} onChange={e=>{setServerId(e.target.value);setDiscovery(null);}}><option value="">Choose an endpoint</option>{servers.map(server=><option key={server.id} value={server.id} disabled={!server.configured}>{server.label} — {server.statusText}</option>)}</select></label><label>Workspace access token<input type="password" autoComplete="off" value={token} onChange={e=>setToken(e.target.value)} placeholder="Kept in memory for this page"/></label></div><div className="apex-actions"><button className="primary-button" disabled={busy||!serverId||!token} onClick={discover}>Discover tools</button><button className="secondary-button" onClick={()=>setToken('')}>Clear token</button></div></>}
   <p role="status" className="apex-note">{message}</p>
   {discovery&&<div className={styles.discovery}><h3>{discovery.server.label} · {discovery.tools.length} tools</h3><p>Negotiated {discovery.server.protocolVersion} · {discovery.pagination.pages} pages{discovery.pagination.truncated?' · Results truncated by the discovery limit':''}</p><label>Filter discovered tools<input value={toolQuery} onChange={e=>setToolQuery(e.target.value)} placeholder="Tool name or description"/></label>{discovery.tools.filter(tool=>`${tool.name} ${tool.description??''}`.toLowerCase().includes(toolQuery.toLowerCase())).map((tool,index)=><details key={`${tool.name}-${index}`}><summary>{tool.name}</summary><p>{tool.description||'No description supplied.'}</p><pre className="apex-json">{JSON.stringify({inputSchema:tool.inputSchema,annotations:tool.annotations},null,2)}</pre></details>)}</div>}
   <details><summary>Protocol and operating limits</summary><p className="apex-note">This adapter supports the 2025 initialization lifecycle over Streamable HTTP with bounded JSON/SSE responses, up to 8 configured endpoints, 5 pages and 100 tools per discovery. It does not implement stateless 2026 discovery, legacy SSE endpoints, stdio process launching, OAuth enrollment, resources, prompts, sampling or tool calls. Gateways must expose a compatible endpoint. Every MCP implementation requires a compatibility check; universal support is not claimed.</p></details>
  </section>
  <section id="skills" className="apex-panel"><div className="apex-panel-heading"><div><h2>Review a skill before adoption</h2><p>Bring SKILL.md from skills.sh or another library. Record its origin and hash without executing its instructions.</p></div><span className="pill">Local review only</span></div>
   <div className="apex-form-grid"><label>Source URL<input disabled={reviewing} type="url" value={sourceUrl} onChange={e=>{setSourceUrl(e.target.value);setReview(null);}} placeholder="https://github.com/owner/repo/blob/…/SKILL.md"/></label><label>Exact revision / commit<input disabled={reviewing} value={revision} onChange={e=>{setRevision(e.target.value);setReview(null);}} placeholder="Immutable source revision"/></label></div>
   <label className={styles.skillInput}>SKILL.md content<textarea disabled={reviewing} rows={9} maxLength={262144} value={skillText} onChange={e=>{setSkillText(e.target.value);setReview(null);}} placeholder={'---\nname: repository-review\ndescription: Review repository structure and evidence.\n---\nSkill instructions…'}/></label>
   <div className="apex-actions"><button className="primary-button" disabled={reviewing||!skillText.trim()} onClick={reviewSkill}>{reviewing?'Reviewing…':'Create review manifest'}</button>{review?.manifest&&<button className="secondary-button" onClick={()=>download('skill-review.json',review.manifest)}><Download size={14}/>Export review</button>}</div>
   {review&&<div role="status" className={styles.review}><strong>{review.valid?'Manifest created · pending human review':'Content needs correction'}</strong>{review.errors.map((error,i)=><p key={`error-${i}`}>{error}</p>)}{review.warnings.map((warning,i)=><p key={`warning-${i}`}>{warning}</p>)}{review.manifest&&<><p>{review.manifest.name} — {review.manifest.description}</p><p>SHA-256: <code>{review.manifest.contentSha256}</code></p><details><summary>Inspect locked manifest</summary><pre className="apex-json">{JSON.stringify(review.manifest,null,2)}</pre></details></>}</div>}
   <p className="apex-note">A hash proves content identity, not trust. Review companion scripts, network access, license, declared tools and actual harness compatibility separately. The bounded parser reports unsupported YAML; it is not a full Agent Skills package validator. Exports contain the pasted skill text, so review it for sensitive content.</p>
  </section>
  <section id="costs" className="apex-panel"><div className="apex-panel-heading"><div><h2>Estimate the complete operating envelope</h2><p>Enter workload-specific quantities and dated rates. Unknown values stay unpriced; use explicit zero for an inapplicable category.</p></div><Link href="/delegation" className="secondary-button">Model & harness rates →</Link></div>
   <div className="apex-table-wrap"><table><thead><tr><th scope="col">Cost category</th><th scope="col">Quantity</th><th scope="col">USD per unit</th><th scope="col">Unit</th></tr></thead><tbody>{costLines.map(([id,label,unit],index)=><tr key={id}><th scope="row">{label}</th><td><input aria-label={`${label} quantity`} type="number" min="0" step="any" value={costs[index].quantity??''} onChange={e=>setCosts(current=>current.map(item=>item.id===id?{...item,quantity:numberOrNull(e.target.value)}:item))}/></td><td><input aria-label={`${label} USD per unit`} type="number" min="0" step="any" value={costs[index].usdPerUnit??''} onChange={e=>setCosts(current=>current.map(item=>item.id===id?{...item,usdPerUnit:numberOrNull(e.target.value)}:item))}/></td><td>{unit}</td></tr>)}</tbody></table></div>
   <div className="apex-form-grid"><label>Expected successful results<input type="number" min="0" step="1" value={successes} onChange={e=>setSuccesses(e.target.value)}/></label><label>Rate evidence / quote reference<input value={rateSource} onChange={e=>setRateSource(e.target.value)} placeholder="Source of your scenario assumptions"/></label><label>Rates as of<input type="date" value={rateDate} onChange={e=>setRateDate(e.target.value)}/></label></div>
   <div className={styles.costResult} aria-live="polite">{costError?<p>{costError}</p>:<><strong>{estimate?.complete?'Scenario total':'Known subtotal'}: ${(estimate?.knownSubtotalUsd??0).toFixed(6)}</strong><span>{estimate?.complete?'All categories explicitly priced.':`${estimate?.missing.length} categories remain unpriced. Total unavailable.`}</span><span>Cost / successful result: {estimate?.costPerSuccessUsd==null?'unavailable':`$${estimate.costPerSuccessUsd.toFixed(6)}`}</span></>}</div>
   <p className="apex-note">Planning estimate in USD, not an invoice or admission budget. Weighted token rates must include input/output/cache differences from Delegation & cost. Include retries and failed work, shared platform allocation, idle capacity and model/tool fees. Graph-extraction LLM tokens belong in model usage; index compute excludes that token charge. Amortize ingestion over a stated query volume. Rates are user supplied and unverified; no live provider pricing or paid calls occur here. The plan includes your pasted skill and rate notes; keep credentials out of those fields.</p>
   <div className="apex-actions"><button className="primary-button" disabled={!!costError||busy||reviewing} onClick={exportPlan}><Download size={15}/>Export interoperability plan</button></div>
  </section>
 </>;
}
