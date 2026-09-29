/**
 * React component for architecture lab.
 *
 * @module ArchitectureLab
 * @packageDocumentation
 */
'use client';
import {useState} from 'react';
import Link from 'next/link';
import {ArrowUpRight,Download,Search} from 'lucide-react';
import {orchestrationEvidence} from '@/lib/orchestration-evidence';
import {retrievalEvidence} from '@/lib/retrieval-evidence';
import {optimizationEvidence} from '@/lib/optimization-evidence';
import {createArchitectureBenchmark,workloadProfiles,type BenchmarkDraft} from '@/lib/architecture-benchmark';
import styles from './ArchitectureLab.module.css';

const candidates=[
 ...orchestrationEvidence.map(entry=>({...entry,key:`orchestration:${entry.id}`,category:'orchestration'})),
 ...retrievalEvidence.map(entry=>({...entry,key:`retrieval:${entry.id}`,category:'retrieval'})),
];
const allowedIds=candidates.map(entry=>entry.key);
const initialDraft:BenchmarkDraft={workload:'repository-change',candidateIds:[],modelRevision:'',datasetRevision:'',environment:'',priceEvidence:'',componentPins:'',trials:3,taskCount:30,activeWorkers:4,budgetUsd:null,minimumSuccessRate:null,maxP95Seconds:null,maxUsdPerSuccess:null};
const evidenceFields=[['modelRevision','Model/provider revision'],['datasetRevision','Held-out dataset / corpus revision'],['componentPins','Framework / store / image pins'],['environment','Hardware, region and index settings'],['priceEvidence','Dated rate and usage-receipt references']] as const;

/**
 * Function SourceReference.
 *
 * @param {{source} source,label - Description of source,label.
 *
 * @example
 * ```typescript
 * const result = SourceReference(...);
 * ```
 */
function SourceReference({source,label}:{source:string;label:string}){return source.startsWith('https://')?<a href={source} target="_blank" rel="noreferrer">{label} <ArrowUpRight size={12}/></a>:<code>{source}</code>;}

/**
 * React component ArchitectureLab.
 *
 *
 * @example
 * ```typescript
 * import { ArchitectureLab } from './module';
 * ```
 */
export default function ArchitectureLab(){
 const [category,setCategory]=useState('orchestration');
 const [query,setQuery]=useState('');
 const [draft,setDraft]=useState<BenchmarkDraft>(initialDraft);
 const visible=candidates.filter(entry=>(category==='all'||entry.category===category)&&`${entry.name} ${entry.role} ${entry.layer}`.toLowerCase().includes(query.toLowerCase()));
 const bottlenecks=optimizationEvidence.filter(entry=>`${entry.name} ${entry.formulation} ${entry.complexity}`.toLowerCase().includes(query.toLowerCase()));
 let plan:ReturnType<typeof createArchitectureBenchmark>|null=null;let error='';
 try{plan=createArchitectureBenchmark(draft,allowedIds);}catch(cause){error=cause instanceof Error?cause.message:'Invalid benchmark design.';}
 function toggle(key:string){setDraft(current=>({...current,candidateIds:current.candidateIds.includes(key)?current.candidateIds.filter(id=>id!==key):[...current.candidateIds,key]}));}
 function exportDesign(){if(!plan)return;const data={...plan,createdAt:new Date().toISOString(),candidateEvidence:candidates.filter(entry=>draft.candidateIds.includes(entry.key)),optimizationHypotheses:optimizationEvidence,localResults:[],note:'Research and experimental design only. No framework or database has been installed, benchmarked or enabled by this export.'};const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const anchor=document.createElement('a');anchor.href=url;anchor.download='apex-architecture-benchmark.json';anchor.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
 return <>
  <div className={styles.layers} aria-label="Architecture layers"><div><span>01 / GOVERNANCE</span><strong>Goals, approval & ownership</strong><p>One authority for task state and spend.</p></div><div><span>02 / ORCHESTRATION</span><strong>Plan, delegate & recover</strong><p>Harnesses and durable workflow engines.</p></div><div><span>03 / RETRIEVAL</span><strong>Find evidence & context</strong><p>Graph expansion, vectors and reranking.</p></div><div><span>04 / OPTIMIZATION</span><strong>Allocate within constraints</strong><p>Measured heuristics and bounded search.</p></div></div>
  <section className="apex-panel">
   <div className="apex-panel-heading"><div><h2>Compare capabilities and evidence</h2><p>Source review dated 27 September 2026. Catalog presence does not mean an adapter is installed or verified locally.</p></div><a href="#benchmark-design" className="secondary-button">Design a benchmark · {draft.candidateIds.length}</a></div>
   <div className={styles.filters}><div role="group" aria-label="Comparison category">{[['orchestration','Orchestration'],['retrieval','GraphRAG & storage'],['optimization','Hard problems'],['all','All projects']].map(([id,label])=><button key={id} aria-pressed={category===id} onClick={()=>setCategory(id)}>{label}</button>)}</div><label><Search size={14}/> Search evidence<input value={query} onChange={event=>setQuery(event.target.value)} placeholder="Framework, storage or bottleneck"/></label></div>
   {category!=='optimization'?<div className={styles.cards}>{visible.map(entry=><article className={styles.card} key={entry.key}>
    <div className={styles.cardHeading}><label><input type="checkbox" checked={draft.candidateIds.includes(entry.key)} onChange={()=>toggle(entry.key)}/><strong>{entry.name}</strong></label><span>{entry.layer}</span></div>
    <p>{entry.role}</p><div className={styles.evidence}><strong>{entry.benchmark.status}</strong><p>{entry.benchmark.description}</p><SourceReference source={entry.benchmark.source} label="Evidence source"/></div>
    <details><summary>Capabilities, tradeoffs & adoption</summary><h4>Useful capabilities</h4><ul>{entry.strengths.map(text=><li key={text}>{text}</li>)}</ul><h4>Boundaries to test</h4><ul>{entry.limits.map(text=><li key={text}>{text}</li>)}</ul>{'retrievalFit' in entry&&<p>{entry.retrievalFit}</p>}<h4>Apex adoption path</h4><p>{entry.adoption}</p><div className={styles.sources}>{entry.sources.map((source,index)=><SourceReference key={source} source={source} label={`Source ${index+1}`}/>)}</div></details>
   </article>)}</div>:<div className={styles.bottlenecks}>{bottlenecks.map(item=><article key={item.id}><span className={styles.complexity}>{item.complexity}</span><h3>{item.name}</h3><p>{item.formulation}</p><div className={styles.split}><div><h4>Practical approach</h4><p>{item.mitigation}</p></div><div><h4>What it does not establish</h4><p>{item.limits}</p></div></div><details><summary>Kernel evidence and measurements</summary><ul>{item.kernelEvidence.map(evidence=><li key={evidence}><code>{evidence}</code></li>)}</ul><h4>Measure</h4><ul>{item.metrics.map(metric=><li key={metric}>{metric}</li>)}</ul><div className={styles.sources}>{item.sources.map((source,index)=><SourceReference key={source} source={source} label={`Reference ${index+1}`}/>)}</div></details></article>)}</div>}
   {((category==='optimization'&&bottlenecks.length===0)||(category!=='optimization'&&visible.length===0))&&<p className="apex-note">No matching evidence. Try a different search or category.</p>}
   <p className="apex-note">A larger agent count does not establish better outcomes. Scheduling, context selection and partitioning can contain NP-hard optimization problems; network latency, quotas, I/O and recovery are operational constraints with different remedies. Existing kernels are candidate heuristics whose behavior must be measured on your workload.</p>
  </section>
  <section id="benchmark-design" className="apex-panel">
   <div className="apex-panel-heading"><div><h2>Build a reproducible comparison</h2><p>Choose candidates above, hold the workload constant, and test one architecture change at a time. This creates a design, not an execution job.</p></div><span className="pill">No paid calls</span></div>
   <div className={styles.selected}><strong>{draft.candidateIds.length} comparison candidates</strong>{draft.candidateIds.length===0?<p>Select at least one project to compare with the workload baseline.</p>:<div>{candidates.filter(entry=>draft.candidateIds.includes(entry.key)).map(entry=><button key={entry.key} onClick={()=>toggle(entry.key)} aria-label={`Remove ${entry.name}`}>{entry.name} ×</button>)}</div>}</div>
   <div className="apex-form-grid"><label>Workload<select value={draft.workload} onChange={event=>setDraft({...draft,workload:event.target.value as BenchmarkDraft['workload']})}>{workloadProfiles.map(profile=><option key={profile.id} value={profile.id}>{profile.name}</option>)}</select></label><label>Held-out tasks<input type="number" min="1" max="10000" value={draft.taskCount} onChange={event=>setDraft({...draft,taskCount:Number(event.target.value)})}/></label><label>Independent trials<input type="number" min="1" max="100" value={draft.trials} onChange={event=>setDraft({...draft,trials:Number(event.target.value)})}/></label><label>Active workers (scenario)<input type="number" min="1" max="64" value={draft.activeWorkers} onChange={event=>setDraft({...draft,activeWorkers:Number(event.target.value)})}/></label><label>Total scenario cap (USD)<input type="number" min="0.000001" step="any" placeholder="Unknown" value={draft.budgetUsd??''} onChange={event=>setDraft({...draft,budgetUsd:event.target.value===''?null:Number(event.target.value)})}/></label></div>
   <p className="apex-note">Worker count is a design assumption, capped at 64 here; it does not change the live four-worker fixture executor or provision a fleet. A scenario cap must be enforced separately by the execution adapter.</p>
   <div className="apex-form-grid"><label>Minimum verified success rate (0–1)<input type="number" min="0.000001" max="1" step="any" placeholder="For example 0.9" value={draft.minimumSuccessRate??''} onChange={event=>setDraft({...draft,minimumSuccessRate:event.target.value===''?null:Number(event.target.value)})}/></label><label>Maximum end-to-end p95 (seconds)<input type="number" min="0.000001" step="any" placeholder="Workload-specific latency target" value={draft.maxP95Seconds??''} onChange={event=>setDraft({...draft,maxP95Seconds:event.target.value===''?null:Number(event.target.value)})}/></label><label>Maximum USD per successful result<input type="number" min="0.000001" step="any" placeholder="Include failed attempts and retries" value={draft.maxUsdPerSuccess??''} onChange={event=>setDraft({...draft,maxUsdPerSuccess:event.target.value===''?null:Number(event.target.value)})}/></label></div>
   <details className={styles.pins}><summary>Pin the workload, environment and prices</summary><div className="apex-form-grid">{evidenceFields.map(([key,label])=><label key={key}>{label}<textarea rows={2} maxLength={4000} value={draft[key]} onChange={event=>setDraft({...draft,[key]:event.target.value})}/></label>)}</div><p className="apex-note">These are unverified research references and are included in the export. Keep secrets out of the fields.</p></details>
   {error?<p role="alert" className="error-text">{error}</p>:plan&&<><div className={styles.baseline}><span>CONTROL BASELINE</span><p>{plan.baseline}</p></div><div className={styles.split}><div><h3>Required measurements</h3><ul>{plan.metrics.map(metric=><li key={metric}>{metric}</li>)}</ul></div><div><h3>Evidence before promotion</h3><ul>{plan.acceptanceGates.map(gate=><li key={gate}>{gate}</li>)}</ul></div></div><p role="status" className="apex-note">{plan.designComplete?'Design fields complete. References still need verification; execution remains disabled.':`Draft design: ${plan.missingEvidence.length} required evidence fields or selections are missing.`}</p></>}
   <div className="apex-actions"><button className="primary-button" disabled={!plan} onClick={exportDesign}><Download size={15}/>Export benchmark design</button><Link className="secondary-button" href="/ecosystem#costs">Estimate full-stack costs</Link><Link className="secondary-button" href="/evaluations">View local fixture results</Link></div>
  </section>
 </>;
}
