/**
 * React component for arena studio.
 *
 * @module ArenaStudio
 * @packageDocumentation
 */
'use client';

import {useEffect,useMemo,useState} from 'react';
import ChartTooltip from './ChartTooltip';
import styles from './ArenaStudio.module.css';

/**
 * Type Row.
 *
 *
 * @example
 * ```typescript
 * import { Row } from './module';
 * ```
 */
type Row=Record<string,unknown>;
/**
 * Type BenchmarkCase.
 *
 *
 * @example
 * ```typescript
 * import { BenchmarkCase } from './module';
 * ```
 */
type BenchmarkCase=Row&{id:string;elapsedMs:number;result:Row};
/**
 * Type Report.
 *
 *
 * @example
 * ```typescript
 * import { Report } from './module';
 * ```
 */
type Report={benchmarkId:string;fixtureSchema:Row;sourceHashes:Record<string,string>;measurementType:string;environment:Row;providerCalls:0;costProvenance:string;cases:BenchmarkCase[];limits:string[]};
/**
 * Type Snapshot.
 *
 *
 * @example
 * ```typescript
 * import { Snapshot } from './module';
 * ```
 */
type Snapshot={schemaVersion:1;runId:string;createdAt:string;report:Report};
const cases=[
 {id:'dag-scheduling',name:'Dependency scheduling',unit:'tasks',description:'Assign a dependency graph under fixture capacity, budget and deadline constraints.'},
 {id:'evidence-selection',name:'Evidence selection',unit:'items',description:'Select evidence items under a token budget and score declared claim coverage.'},
 {id:'file-conflict-waves',name:'Coding conflict waves',unit:'tasks',description:'Schedule declared read/write tasks into conflict-aware waves.'},
 {id:'capacity-recommendation',name:'Inference capacity',unit:'samples',description:'Recommend concurrency from synthetic throughput, latency, utilization and queue samples.'},
 {id:'paired-promotion-gate',name:'Held-out promotion gate',unit:'paired tasks',description:'Compare a supplied fixture candidate against a baseline with conservative uncertainty bounds.'},
] as const;
/**
 * Function isRow.
 *
 * @param v - Description of v.
 * @returns {v is Row} Description of return value.
 *
 * @example
 * ```typescript
 * const result = isRow(...);
 * ```
 */
function isRow(v:unknown):v is Row{return !!v&&typeof v==='object'&&!Array.isArray(v);}
/**
 * Function isReport.
 *
 * @param v - Description of v.
 * @returns {v is Report} Description of return value.
 *
 * @example
 * ```typescript
 * const result = isReport(...);
 * ```
 */
function isReport(v:unknown):v is Report{return isRow(v)&&typeof v.benchmarkId==='string'&&isRow(v.fixtureSchema)&&isRow(v.sourceHashes)&&Object.values(v.sourceHashes).every(hash=>typeof hash==='string')&&typeof v.measurementType==='string'&&isRow(v.environment)&&v.providerCalls===0&&typeof v.costProvenance==='string'&&Array.isArray(v.cases)&&v.cases.length===5&&Array.isArray(v.limits)&&v.limits.every(item=>typeof item==='string')&&v.cases.every(c=>isRow(c)&&['dag-scheduling','evidence-selection','file-conflict-waves','capacity-recommendation','paired-promotion-gate'].includes(String(c.id))&&typeof c.elapsedMs==='number'&&Number.isFinite(c.elapsedMs)&&c.elapsedMs>=0&&isRow(c.result));}
/**
 * Function encode.
 *
 * @param value - Description of value.
 *
 * @example
 * ```typescript
 * const result = encode(...);
 * ```
 */
function encode(value:unknown){const bytes=new TextEncoder().encode(JSON.stringify(value));let binary='';for(const byte of bytes)binary+=String.fromCharCode(byte);return btoa(binary).replaceAll('+','-').replaceAll('/','_').replace(/=+$/,'');}
/**
 * Function decode.
 *
 * @param {string} value - Description of value.
 * @returns {unknown} Description of return value.
 *
 * @example
 * ```typescript
 * const result = decode(...);
 * ```
 */
function decode(value:string):unknown{if(value.length>18000)throw Error('This shared result is too large to open safely.');const normalized=value.replaceAll('-','+').replaceAll('_','/');const binary=atob(normalized.padEnd(Math.ceil(normalized.length/4)*4,'='));const bytes=Uint8Array.from(binary,c=>c.charCodeAt(0));return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));}
/**
 * Function caseInput.
 *
 * @param {Row} row - Description of row.
 *
 * @example
 * ```typescript
 * const result = caseInput(...);
 * ```
 */
function caseInput(row:Row){const result=isRow(row.result)?row.result:{};return Number(row.inputTasks??row.inputItems??row.inputTelemetrySamples??result.taskCountHeldout??0);}
/**
 * Function duration.
 *
 * @param value - Description of value.
 *
 * @example
 * ```typescript
 * const result = duration(...);
 * ```
 */
function duration(value:unknown){return typeof value==='number'&&Number.isFinite(value)?value.toFixed(3)+' ms':'Not measured';}
/**
 * Function json.
 *
 * @param value - Description of value.
 *
 * @example
 * ```typescript
 * const result = json(...);
 * ```
 */
function json(value:unknown){return JSON.stringify(value,null,2);}
/**
 * Function moneyMicrousd.
 *
 * @param value - Description of value.
 *
 * @example
 * ```typescript
 * const result = moneyMicrousd(...);
 * ```
 */
function moneyMicrousd(value:unknown){return typeof value==='number'&&Number.isFinite(value)?'$'+(value/1_000_000).toFixed(6):'Unknown';}
/**
 * Function runDigest.
 *
 * @param {Report} report - Description of report.
 * @param {string} createdAt - Description of createdAt.
 *
 * @example
 * ```typescript
 * const result = runDigest(..., ...);
 * ```
 */
async function runDigest(report:Report,createdAt:string){const data=new TextEncoder().encode(JSON.stringify({report,createdAt}));const digest=await crypto.subtle.digest('SHA-256',data);return [...new Uint8Array(digest)].map(x=>x.toString(16).padStart(2,'0')).join('');}
/**
 * React component ArenaStudio.
 *
 *
 * @example
 * ```typescript
 * import { ArenaStudio } from './module';
 * ```
 */
export default function ArenaStudio(){
 const[token,setToken]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState(''),[snapshot,setSnapshot]=useState<Snapshot|null>(null),[shared,setShared]=useState(false),[copied,setCopied]=useState(false);
 useEffect(()=>{const value=new URLSearchParams(location.hash.slice(1)).get('run');if(!value)return;let active=true;void(async()=>{try{const raw=decode(value);if(!isRow(raw)||raw.schemaVersion!==1||typeof raw.runId!=='string'||!/^[a-f0-9]{64}$/.test(raw.runId)||typeof raw.createdAt!=='string'||Number.isNaN(Date.parse(raw.createdAt))||!isReport(raw.report))throw Error('Shared result schema is not supported.');if(await runDigest(raw.report,raw.createdAt)!==raw.runId)throw Error('Shared run integrity check failed.');if(active){setSnapshot(raw as Snapshot);setShared(true);}}catch(cause){if(active)setError(cause instanceof Error?cause.message:'Could not open this shared run.');}})();return()=>{active=false;}},[]);
 const sorted=[...(snapshot?.report.cases||[])].sort((a,b)=>Number(a.elapsedMs)-Number(b.elapsedMs));const fastest=sorted[0];
 const gateCase=snapshot?.report.cases.find(row=>row.id==='paired-promotion-gate');const gate=isRow(gateCase?.result)?gateCase.result:null;const held=isRow(gate?.heldoutSummary)?gate.heldoutSummary:null;const gateDecision=isRow(gate?.promotionDecision)?gate.promotionDecision:null;
 const shareHref=useMemo(()=>snapshot?location.origin+location.pathname+'#run='+encode(snapshot):'',[snapshot]);
 async function run(){setError('');setCopied(false);setBusy(true);try{if(!token.trim())throw Error('Enter the private workspace execution token to run the local benchmark.');const response=await fetch('/api/optimization',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+token.trim()},body:JSON.stringify({action:'benchmark'})});const body=await response.json();if(!response.ok)throw Error(typeof body.error==='string'?body.error:'Benchmark run failed.');if(!isReport(body.result))throw Error('The benchmark returned an unsupported evidence report.');const createdAt=new Date().toISOString();const runId=await runDigest(body.result,createdAt);setSnapshot({schemaVersion:1,runId,createdAt,report:body.result});setShared(false);history.replaceState(null,'',location.pathname); }catch(cause){setError(cause instanceof Error?cause.message:'Benchmark failed.');}finally{setBusy(false);}}
 async function copyLink(){setCopied(true);try{history.replaceState(null,'','#run='+encode(snapshot));await navigator.clipboard.writeText(shareHref);setError('');}catch{setError('Copy was blocked by the browser. Select the share link below and copy it manually.');}}
 function download(){if(!snapshot)return;const blob=new Blob([json(snapshot)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='apexgraphswarm-'+snapshot.runId.slice(0,12)+'.json';a.click();URL.revokeObjectURL(url);}
 const maxDuration=Math.max(0,...(snapshot?.report.cases||[]).map(c=>Number(c.elapsedMs)||0));
 return <div className={styles.arena}>
  <section className="apex-panel" aria-labelledby="arena-run-title"><div className="apex-panel-heading"><div><span className="eyebrow">REPRODUCIBLE CHALLENGE / LOCAL FIXTURE</span><h2 id="arena-run-title">Run the five track challenge</h2><p>One pinned suite exercises scheduling, evidence, conflict planning, capacity advice and held-out evaluation.</p></div><span className={styles.badge}>{snapshot?'RUN SNAPSHOT':'READY TO RUN'}</span></div>
   <div className={styles.tracks}>{cases.map((item,index)=><article key={item.id}><span>0{index+1}</span><h3>{item.name}</h3><p>{item.description}</p></article>)}</div>
   <div className={styles.runControls}><label>Private workspace execution token<input type="password" autoComplete="off" value={token} onChange={e=>setToken(e.target.value)} placeholder="Kept in memory only" disabled={busy}/></label><button className="primary-button" onClick={()=>void run()} disabled={busy||!token.trim()}>{busy?'Running bounded local suite…':'Run local benchmark'}</button></div>
   <p className="apex-note">Runs the committed Python fixture; it makes no model or provider calls. The API token is sent only to this workspace endpoint and is not included in a result link or export.</p>
   {busy&&<p role="status">Measuring the deterministic fixture cases…</p>}{error&&<p role="alert" className="error-text">{error}</p>}
  </section>
  {snapshot&&<>
   <section className="apex-panel" aria-labelledby="arena-result-title"><div className="apex-panel-heading"><div><span className="eyebrow">{shared?'SHARED SNAPSHOT':'MEASURED ON THIS RUN'}</span><h2 id="arena-result-title">Challenge evidence</h2><p>Run {snapshot.runId.slice(0,20)}… · {new Date(snapshot.createdAt).toLocaleString()}</p></div><div className={styles.actions}><button className="secondary-button" onClick={()=>void copyLink()}>{copied?'Link copied':'Copy share link'}</button><button className="secondary-button" onClick={download}>Download JSON</button></div></div>
    <p className={styles.honesty}><strong>Unsigned, self-contained snapshot.</strong> The link includes fixture outputs, Python/platform versions and source hashes so recipients can inspect and rerun it. It excludes the access token. Anyone with the URL can read the encoded report; this local app does not sign results or operate a hosted leaderboard.</p>
    <div className={styles.runStats}><div><span>Suite</span><strong>{snapshot.report.benchmarkId}</strong></div><div><span>Provider calls</span><strong>0</strong></div><div><span>Cases</span><strong>{snapshot.report.cases.length}</strong></div><div><span>Shortest case time</span><strong>{fastest?.id||'—'} · {duration(fastest?.elapsedMs)}</strong></div></div>
    {copied&&<label className={styles.shareField}>Share URL<input readOnly value={shareHref} onFocus={e=>e.currentTarget.select()}/></label>}
    <div className={styles.caseList}><h3>Track measurements</h3>{sorted.map(row=>{const meta=cases.find(item=>item.id===row.id)!;const width=maxDuration>0?Math.max(2,Number(row.elapsedMs)/maxDuration*100):2;return <article key={row.id}><div className={styles.caseHeading}><div><h4>{meta.name}</h4><p>{Number.isSafeInteger(caseInput(row))?caseInput(row)+' '+meta.unit+' in fixture':meta.description}</p></div><strong>{duration(row.elapsedMs)}</strong></div><ChartTooltip title={meta.name+' · '+duration(row.elapsedMs)} details={[{label:'Fixture case',value:row.id},{label:'Input size',value:caseInput(row)+' '+meta.unit},{label:'Observed local time',value:duration(row.elapsedMs)},{label:'Source classification',value:'Deterministic synthetic fixture'},{label:'Provider calls',value:'0'}]}><button className={styles.barHit} aria-label={meta.name+', '+duration(row.elapsedMs)} type="button"><span style={{width:width+'%'}}/></button></ChartTooltip><details><summary>Inspect measured output</summary><pre className="apex-json">{json(row.result)}</pre></details></article>})}</div>
    {held&&gate&&gateDecision&&<div className={styles.gate}><h3>Promotion gate example</h3><p>Both options are synthetic evaluator fixtures with 64 held-out paired tasks. The uncertainty gates correctly withhold promotion in this small demo.</p><div className={styles.compare}><div><span>Baseline observed cost / accepted task</span><strong>{moneyMicrousd((held.baseline as Row|undefined)?.costPerAcceptedMicrousd)}</strong></div><div><span>Candidate observed cost / accepted task</span><strong>{moneyMicrousd((held.candidate as Row|undefined)?.costPerAcceptedMicrousd)}</strong></div><div><span>Gate result</span><strong>{gateDecision.promote===true?'Promoted':'Not promoted'}</strong></div></div><p className={styles.caveat}>Fixture microUSD values are arithmetic examples, not API prices or bills. Lower fixture cost alone cannot pass held-out quality and noninferiority checks. Sealed tasks were not used to select this candidate.</p></div>}
    <details className={styles.provenance}><summary>Reproduction pins and limits</summary><dl><div><dt>Measurement</dt><dd>{snapshot.report.measurementType}</dd></div><div><dt>Environment</dt><dd>{json(snapshot.report.environment)}</dd></div><div><dt>Fixture schema</dt><dd>{json(snapshot.report.fixtureSchema)}</dd></div><div><dt>Source SHA-256</dt><dd><pre>{json(snapshot.report.sourceHashes)}</pre></dd></div><div><dt>Cost provenance</dt><dd>{snapshot.report.costProvenance}</dd></div></dl><ul>{snapshot.report.limits.map(item=><li key={item}>{item}</li>)}</ul></details>
   </section>
  </>}
 </div>;
}
