/**
 * React component for analytics studio.
 *
 * @module AnalyticsStudio
 * @packageDocumentation
 */
'use client';
import {useCallback,useEffect,useRef,useState} from 'react';
import {downloadJSON} from '@/lib/graph';
import {parseAnalyticsImport,analyticsCSV,type AnalyticsEvent} from '@/lib/analytics-import';
import {type AnalyticsReport,dollars,decimal} from '@/lib/analytics-types';
import {TrendChart,Histogram,ScatterChart,ActivityHeatmap,ForecastChart} from './AnalyticsCharts';
import styles from './AnalyticsStudio.module.css';
import AnalyticsRelationshipGraph from './AnalyticsRelationshipGraph';
import AnalyticsVisualGallery from './AnalyticsVisualGallery';
const views=['Overview','Visualizations','Statistics','Predictions','Relationships','Data & methods'] as const;
/**
 * Type View.
 *
 *
 * @example
 * ```typescript
 * import { View } from './module';
 * ```
 */
type View=typeof views[number];
/**
 * Function saveText.
 *
 * @param {string} name - Description of name.
 * @param {string} text - Description of text.
 *
 * @example
 * ```typescript
 * const result = saveText(..., ...);
 * ```
 */
function saveText(name:string,text:string){const url=URL.createObjectURL(new Blob([text],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
/**
 * React component AnalyticsStudio.
 *
 *
 * @example
 * ```typescript
 * import { AnalyticsStudio } from './module';
 * ```
 */
export default function AnalyticsStudio(){
 const [report,setReport]=useState<AnalyticsReport|null>(null),[view,setView]=useState<View>('Overview');
 const [source,setSource]=useState<'live'|'import'|'demo'>('live'),[token,setToken]=useState(''),[days,setDays]=useState(30),[tool,setTool]=useState('');
 const [rows,setRows]=useState<AnalyticsEvent[]>([]),[busy,setBusy]=useState(false),[error,setError]=useState(''),[message,setMessage]=useState(''),[dirty,setDirty]=useState(false);
 const [continuous,setContinuous]=useState(false),[lastRefresh,setLastRefresh]=useState<string|null>(null),[metric,setMetric]=useState<'cost'|'attempts'>('cost');
 const [revenue,setRevenue]=useState(''),[overhead,setOverhead]=useState('');
 const request=useRef<AbortController|null>(null),running=useRef(false);
 const refresh=useCallback(async()=>{
  if(running.current)return;if(!token){setError('Enter the private workspace execution token to read recorded data or analyze an import.');setContinuous(false);return;}
  if(source==='demo')return;
  running.current=true;const controller=new AbortController();request.current=controller;setBusy(true);setError('');
  try{const response=await fetch('/api/analytics',{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`},body:JSON.stringify({source,days,...(tool?{tool}:{}),...(source==='import'?{rows}:{})}),signal:controller.signal});const body=await response.json();if(!response.ok)throw Error(body.error||'Analytics could not be loaded.');setReport(body.result);setDirty(false);setLastRefresh(new Date().toISOString());setMessage('Snapshot refreshed. No model calls or state mutations were performed.');}
  catch(error){if(!controller.signal.aborted){setError(error instanceof Error?error.message:'Analytics failed.');setContinuous(false);setDirty(true);}}
  finally{if(request.current===controller){setBusy(false);running.current=false;}}
 },[source,days,tool,token,rows]);
 useEffect(()=>{if(!continuous||source!=='live')return;const timer=setInterval(()=>{if(document.visibilityState==='visible')void refresh();},30000);return()=>clearInterval(timer);},[continuous,source,refresh]);
 useEffect(()=>()=>request.current?.abort(),[]);
 async function demo(){setContinuous(false);setBusy(true);setError('');try{const response=await fetch('/analytics-demo.json');if(!response.ok)throw Error('The synthetic demo asset is unavailable.');const data=await response.json();setReport(data);setSource('demo');setTool('');setDirty(false);setLastRefresh(null);setMessage('Synthetic example loaded. These are deterministic fixtures, not your operational results.');}catch(error){setError(error instanceof Error?error.message:'Demo unavailable.');}finally{setBusy(false);}}
 async function importFile(file:File){setError('');setContinuous(false);try{if(file.size>1048576)throw Error('Imports are limited to 1 MiB.');const parsed=parseAnalyticsImport(await file.text(),file.name);setRows(parsed);setSource('import');setDirty(true);setMessage(`Validated ${parsed.length.toLocaleString()} event rows in memory. Select Refresh snapshot to analyze. Nothing has been written to the ledger.`);}catch(error){setError(error instanceof Error?error.message:'Import failed.');}}
 function template(){const now=Math.floor(Date.now()/1000);saveText('apex-analytics-event-template.csv',analyticsCSV([{attemptId:'example-attempt',taskId:'example-task',tool:'example-tool',resource:'example-resource',startedAt:now-60,settledAt:now,outcome:'succeeded',actualCostMicrousd:null}]));}
 const stats=report?.kpis,unknown=Boolean(report&&(report.quality.unknownCostRows>0||report.quality.truncated||report.quality.invalidRows>0||report.quality.selectionKnownCoverage!==true));
 const revenueNumber=Number(revenue),overheadNumber=Number(overhead),scenarioValid=Boolean(report&&!unknown&&revenue.trim()&&overhead.trim()&&Number.isFinite(revenueNumber)&&Number.isFinite(overheadNumber)&&revenueNumber>=0&&overheadNumber>=0&&revenueNumber<=1e9&&overheadNumber<=1e12&&report.kpis.succeeded>0);
 const modeledRevenue=scenarioValid?report!.kpis.succeeded*revenueNumber:null;
 const modeledCost=scenarioValid?report!.kpis.knownCostMicrousd/1e6+overheadNumber:null;
 return <div className={styles.studio}>
 <section className={styles.toolbar} aria-label="Analytics data controls"><div className={styles.toolbarHeading}><div><span className="eyebrow">CONTINUOUS INTELLIGENCE</span><h2>Your evidence, in context.</h2></div><span className={styles.badge}>{report?.source==='demo'?'SYNTHETIC EXAMPLE':report?`${report.source.toUpperCase()} SNAPSHOT`:'NO DATA LOADED'}</span></div>
 <div className={styles.controls}><label>Data source<select value={source} disabled={busy} onChange={e=>{setSource(e.target.value as typeof source);setContinuous(false);setDirty(true);}}><option value="live">Recorded execution ledger</option><option value="import">Imported events</option><option value="demo">Synthetic example</option></select></label><label>Analysis window<select value={days} disabled={busy||source==='demo'} onChange={e=>{setDays(Number(e.target.value));setDirty(true);}}><option value={7}>Last 7 days</option><option value={30}>Last 30 days</option><option value={90}>Last 90 days</option><option value={365}>Last 365 days</option></select></label><label>Tool filter<select value={tool} disabled={busy||source==='demo'} onChange={e=>{setTool(e.target.value);setDirty(true);}}><option value="">All tools</option>{report?.availableTools.map(item=><option key={item}>{item}</option>)}</select></label><label>Private workspace token<input type="password" autoComplete="off" value={token} onChange={e=>setToken(e.target.value)} placeholder="Kept in memory only" disabled={busy}/></label></div>
 <div className={styles.actions}><button className="primary-button" disabled={busy||(source==='import'&&!rows.length)} onClick={()=>void(source==='demo'?demo():refresh())}>{busy?'Computing…':'Refresh snapshot'}</button><button className="secondary-button" disabled={busy} onClick={()=>void demo()}>Explore synthetic demo</button><label className={styles.toggle}><input type="checkbox" checked={continuous} disabled={busy||source!=='live'||!token} onChange={e=>setContinuous(e.target.checked)}/>Refresh every 30 seconds</label><span className={styles.freshness}>{lastRefresh?`Fetched ${new Date(lastRefresh).toLocaleTimeString()}`:'On-demand snapshot'}</span></div>
 <p className={styles.note}>Automatic refresh runs only while this page is visible and stops after an error. It does not configure a background scheduler. Imported rows are analyzed in memory.</p>
 {message&&<p role="status" className={styles.notice}>{message}</p>}{error&&<p role="alert" className={styles.error}>{error}</p>}{dirty&&report&&<p className={styles.warning}>Showing the previous snapshot. Refresh to apply the current source and filters.</p>}
 </section>
 {!report?<section className={styles.empty}><span className="eyebrow">START WITH A QUESTION</span><h2>Where does your swarm spend time and money?</h2><p>Explore a clearly labeled synthetic dataset, connect the local execution ledger, or import event records. Every visualization keeps its provenance, coverage and assumptions visible.</p><div className={styles.emptyGrid}>{['Operational intelligence','Statistical diagnostics','Predictive planning','Graph relationships'].map((label,i)=><div key={label}><span>0{i+1}</span><h3>{label}</h3><p>{['Cost, throughput and cohort comparisons','Latency, dispersion and paired observations','Baseline forecasts with chronological holdout checks','Tool/resource activity with inspectable connections'][i]}</p></div>)}</div><button className="secondary-button" onClick={()=>setView('Data & methods')}>Review import schema</button></section>:<>
 <section className={styles.kpis} aria-label="Analytics key indicators">{[
 ['Attempts',stats!.attempts.toLocaleString(),`${stats!.succeeded} succeeded · ${stats!.failed} failed`],
 ['Known recorded cost',dollars(stats!.knownCostMicrousd),`${report.quality.unknownCostRows} unresolved cost records`],
 ['Success share',stats!.successRate==null?'Unknown':decimal(stats!.successRate*100,'%'),'Succeeded / selected attempts, including open attempts'],
 ['p95 settled latency',decimal(report.latency.p95,'s'),`${report.latency.count} observations${report.latency.sampled?' · sampled':''}`],
 ['Cost / success',dollars(stats!.costPerSuccessMicrousd),'All known attempt costs / successful attempts'],
 ].map(([label,value,detail])=><article key={label}><span>{label}</span><strong>{value}</strong><small>{detail}</small></article>)}</section>
 {unknown&&<p className={styles.warning}>Incomplete evidence: cost totals are known amounts only. Forecasts and complete unit economics are withheld when coverage is insufficient.</p>}
 </>}
 <nav className={styles.tabs} aria-label="Analytics views">{views.map(item=><button key={item} aria-pressed={view===item} onClick={()=>setView(item)}>{item}</button>)}</nav>
 {report&&view==='Overview'&&<><section className={styles.panel}><div className={styles.panelHeading}><div><span className="eyebrow">PERFORMANCE OVER TIME</span><h2>Daily operating profile</h2></div><label>Trend metric<select value={metric} onChange={e=>setMetric(e.target.value as typeof metric)}><option value="cost">Known cost</option><option value="attempts">Attempts</option></select></label></div><TrendChart report={report} metric={metric}/><details><summary>Inspect daily values</summary><div className={styles.tableWrap}><table><thead><tr><th>UTC day</th><th>Attempts</th><th>Succeeded</th><th>Known cost</th><th>Unknown</th></tr></thead><tbody>{report.daily.map(row=><tr key={row.date}><td>{row.date}</td><td>{row.attempts}</td><td>{row.succeeded}</td><td>{dollars(row.knownCostMicrousd)}</td><td>{row.unknownCostRows}</td></tr>)}</tbody></table></div></details></section><section className={styles.panel}><h2>Tool and resource economics</h2><p>Compare observed workload mix. Differences are descriptive; cohorts are not randomized experiments.</p><div className={styles.tableWrap}><table><thead><tr><th>Tool / resource</th><th>Attempts</th><th>Successes</th><th>Known cost</th><th>Unknown</th><th>Mean latency</th></tr></thead><tbody>{report.cohorts.map((row,i)=><tr key={i}><td><strong>{row.tool}</strong><small>{row.resource}</small></td><td>{row.attempts}</td><td>{row.succeeded}</td><td>{dollars(row.knownCostMicrousd)}</td><td>{row.unknownCostRows}</td><td>{decimal(row.meanLatencySeconds,'s')}</td></tr>)}</tbody></table></div></section><section className={styles.panel}><h2>Unit economics scenario</h2><p>Enter your assumptions in USD. Success means an execution attempt succeeded; it does not establish customer revenue or business value.</p><div className={styles.controls}><label>Assumed revenue per successful attempt<input type="number" min="0" max="1000000000" step="any" value={revenue} onChange={e=>setRevenue(e.target.value)} placeholder="USD / successful attempt"/></label><label>Allocated overhead for this window<input type="number" min="0" max="1000000000000" step="any" value={overhead} onChange={e=>setOverhead(e.target.value)} placeholder="USD, including labor and infrastructure"/></label></div>{scenarioValid?<div className={styles.scenario}><p>Modeled revenue <strong>${decimal(modeledRevenue)}</strong></p><p>Recorded cost + assumed overhead <strong>${decimal(modeledCost)}</strong></p><p>Modeled contribution <strong>${decimal(modeledRevenue!-modeledCost!)}</strong></p><p>Break-even revenue / success <strong>${decimal(modeledCost!/report.kpis.succeeded)}</strong></p></div>:<p>Enter both assumptions and use complete cost records with at least one successful attempt to calculate this scenario.</p>}</section></>}
 {report&&view==='Visualizations'&&<AnalyticsVisualGallery report={report}/>}
 {report&&view==='Statistics'&&<><div className={styles.twoColumns}><section className={styles.panel}><span className="eyebrow">DISTRIBUTION</span><h2>Where latency accumulates</h2><p>Median {decimal(report.latency.p50,'s')} · mean {decimal(report.latency.mean,'s')} · standard deviation {decimal(report.latency.stddev,'s')}</p><Histogram report={report}/><p>Settled durations only. Open attempts are excluded; tail estimates may be sampled.</p></section><section className={styles.panel}><span className="eyebrow">PAIRED OBSERVATIONS</span><h2>Cost and duration</h2><ScatterChart report={report}/></section></div><section className={styles.panel}><h2>Activity rhythm</h2><ActivityHeatmap report={report}/></section><section className={styles.panel}><h2>Unusual daily spending</h2><p>Robust descriptive flags prompt investigation; they are not proof of a fault, fraud or a causal event.</p>{report.anomalies.length?<ul>{report.anomalies.map((row,i)=><li key={i}><strong>{row.date}</strong> · {dollars(row.value)} · {row.reason}</li>)}</ul>:<p>No anomaly flags, or insufficient complete history to assess them. See methods for eligibility rules.</p>}</section></>}
 {report&&view==='Predictions'&&<section className={styles.panel}><span className="eyebrow">PREDICTIVE BASELINE / {report.forecast.status}</span><h2>Plan with uncertainty in view.</h2><p>{report.forecast.method}</p><ForecastChart report={report}/><div className={styles.scenario}><p>Chronological holdout MAE <strong>{dollars(report.forecast.backtestMAE)}</strong></p><p>Naive baseline MAE <strong>{dollars(report.forecast.naiveMAE)}</strong></p></div><p>Lower holdout error is better. A single local holdout does not prove future performance; this forecast never changes routing or spending limits.</p>{report.forecast.points.length>0&&<div className={styles.tableWrap}><table><thead><tr><th>UTC day</th><th>Predicted cost</th><th>Heuristic low</th><th>Heuristic high</th></tr></thead><tbody>{report.forecast.points.map(row=><tr key={row.date}><td>{row.date}</td><td>{dollars(row.predictedMicrousd)}</td><td>{dollars(row.lowerMicrousd)}</td><td>{dollars(row.upperMicrousd)}</td></tr>)}</tbody></table></div>}<ul>{report.forecast.limitations.map(item=><li key={item}>{item}</li>)}</ul></section>}
 {report&&view==='Relationships'&&<section className={styles.panel}><span className="eyebrow">OBSERVED INTERACTIONS</span><h2>Follow the work through the graph.</h2><AnalyticsRelationshipGraph report={report}/><a href="/swarm">Open execution-level authorization and cost evidence →</a></section>}
 {view==='Data & methods'&&<><section className={styles.panel}><h2>Bring your own event data</h2><p>CSV or JSON · 1 MiB per file · 10,000 rows. Timestamps are Unix seconds, costs are integer micro-USD, and blank costs remain unknown. Re-importing does not write to or duplicate the execution ledger.</p><div className={styles.actions}><label>Import event dataset<input type="file" accept=".csv,.json,text/csv,application/json" disabled={busy} onChange={e=>{const file=e.target.files?.[0];if(file)void importFile(file);e.target.value='';}}/></label><button className="secondary-button" onClick={template}>Download event template</button></div><pre className={styles.schema}>attemptId, taskId, tool, resource, startedAt, settledAt, outcome, actualCostMicrousd</pre><p>The event schema supports operational BI. CRM, product revenue and warehouse tables need an explicit mapping to avoid mixing customers, tasks and attempts.</p></section><section className={styles.panel}><h2>Scale and evidence contract</h2><p>The Python engine reads SQLite through bounded batches and keeps a bounded statistical sample. The browser receives aggregates and a limited graph; it does not load a full warehouse.</p><p>Live queries are read-only, server-path controlled and limited to 15 seconds at the web boundary, with at most two concurrent requests per server process. This is a local analytics foundation, not a claim of distributed big-data throughput.</p>{report&&<><dl className={styles.quality}>{Object.entries(report.quality).map(([key,value])=><div key={key}><dt>{key}</dt><dd>{typeof value==='object'?JSON.stringify(value):String(value)}</dd></div>)}</dl><ul>{report.limitations.map(item=><li key={item}>{item}</li>)}</ul></>}<a href="/optimization">Compare algorithms and held-out promotion gates →</a></section></>}
 {report&&<footer className={styles.footer}><span>Window starts {new Date(report.windowStart).toISOString().slice(0,10)} UTC · {report.quality.selectedRows.toLocaleString()} selected rows</span><button className="secondary-button" onClick={()=>downloadJSON('apex-analytics-evidence.json',report)}>Export aggregate evidence</button></footer>}
 </div>;
}
