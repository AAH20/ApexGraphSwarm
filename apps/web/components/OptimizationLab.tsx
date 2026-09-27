'use client';
import {useRef,useState} from 'react';
import {downloadJSON} from '@/lib/graph';
import {optimizationExamples} from '@/lib/optimization-examples';
import styles from './OptimizationLab.module.css';
import OptimizationResults from './OptimizationResults';

type Result=Record<string,unknown>;
function text(value:unknown){return typeof value==='string'||typeof value==='number'||typeof value==='boolean'?String(value):value===null?'Unknown':JSON.stringify(value);}
export default function OptimizationLab(){
 const [selected,setSelected]=useState(0),[source,setSource]=useState(JSON.stringify(optimizationExamples[0].payload,null,2));
 const [token,setToken]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const [verification,setVerification]=useState<Result|null>(null);
 const [result,setResult]=useState<Result|null>(null),[submitted,setSubmitted]=useState<Result|null>(null),[focus,setFocus]=useState('');
 const resultRef=useRef<HTMLHeadingElement>(null);
 const example=optimizationExamples[selected];
 function choose(index:number){setSelected(index);setSource(JSON.stringify(optimizationExamples[index].payload,null,2));setResult(null);setSubmitted(null);setError('');setFocus('');setVerification(null);}
 async function run(){
  setError('');setBusy(true);setResult(null);setSubmitted(null);setFocus('');setVerification(null);
  try{
   const payload=JSON.parse(source);if(!payload||Array.isArray(payload)||typeof payload!=='object')throw Error('Enter a JSON object.');
   const response=await fetch('/api/optimization',{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`},body:JSON.stringify(payload)});
   const body=await response.json();if(!response.ok)throw Error(body.error||'Experiment failed.');
   setResult(body.result);setSubmitted(payload);requestAnimationFrame(()=>resultRef.current?.focus());
  }catch(error){setError(error instanceof Error?error.message:'Experiment failed.');}finally{setBusy(false);}
 }
 async function recheckRepository(){
  if(!result)return;setBusy(true);setError('');setVerification(null);
  try{const response=await fetch('/api/optimization',{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`},body:JSON.stringify({action:'verifyRepositoryConflicts',plan:result})});const body=await response.json();if(!response.ok)throw Error(body.error||'Evidence verification failed.');setVerification(body.result);}
  catch(error){setError(error instanceof Error?error.message:'Evidence verification failed.');}finally{setBusy(false);}
 }
 const taskInput=submitted?.tasks ?? (submitted?.problem && typeof submitted.problem==='object' ? (submitted.problem as Result).tasks : undefined);
 const tasks=Array.isArray(taskInput)?taskInput.filter((v):v is Record<string,unknown>=>!!v&&typeof v==='object'&&!Array.isArray(v)):[];
 const focused=tasks.find(task=>task.id===focus);
 const graphTasks=tasks.slice(0,64);
 const locations=new Map(graphTasks.map((task,index)=>[String(task.id),{x:25+(index%4)*195,y:25+Math.floor(index/4)*100}]));
 const summary=result?Object.entries(result).filter(([,v])=>v===null||['string','number','boolean'].includes(typeof v)):[];
 return <>
  <section className="apex-panel">
   <div className="apex-panel-heading"><div><h2>Local experiment workbench</h2><p>Standard-library optimizers · explicit constraints · no provider calls</p></div><span className="pill">Bounded experiments</span></div>
   <div className={styles.choices} role="group" aria-label="Experiment templates">{optimizationExamples.map((item,index)=><button key={item.title} type="button" aria-pressed={selected===index} disabled={busy} className={selected===index?styles.chosen:''} onClick={()=>choose(index)}>{item.title}</button>)}</div>
   <h3>{example.title}</h3><p className={styles.description}>{example.description}</p>
   <div className={styles.layout}><div><label className={styles.label} htmlFor="experiment-json">Editable experiment JSON</label><textarea id="experiment-json" className={styles.editor} spellCheck={false} value={source} disabled={busy} onChange={event=>setSource(event.target.value)}/></div><aside className={styles.context}><h3>What this establishes</h3><p>{example.establishes}</p><h3>What remains unmeasured</h3><p>{example.limit}</p><p>Costs in templates are illustrative microUSD inputs. 1,000,000 microUSD = $1. They are not current model prices or billing receipts.</p><p>128 KiB request limit · 15-second process deadline · at most two local experiments per web process.</p></aside></div>
   <div className={styles.controls}><label className={styles.label}>Private workspace execution token<input type="password" autoComplete="off" value={token} disabled={busy} onChange={event=>setToken(event.target.value)} placeholder="INTEGRATION_ACCESS_TOKEN"/></label><button className="primary-button" disabled={busy||!token} onClick={()=>void run()}>{busy?'Running local experiment…':'Run experiment'}</button></div>
   <p className="apex-note">The token stays in memory. Running an experiment does not deploy a plan, issue credentials, launch coding agents or change your inference cluster.</p>
   {busy&&<p role="status">Computing and checking the local result…</p>}{error&&<p role="alert" className="error-text">{error}</p>}
  </section>
  {result&&<section className="apex-panel" aria-label="Experiment result"><div className="apex-panel-heading"><div><span className="eyebrow">LOCAL RESULT / INSPECTABLE EVIDENCE</span><h2 ref={resultRef} tabIndex={-1}>Experiment complete</h2><p>Results identify supplied inputs, configured telemetry and measured computation.</p></div><button className="secondary-button" onClick={()=>downloadJSON('apex-optimization-evidence.json',{input:submitted,result,...(verification?{verification}:{} )})}>Export input & result</button></div>
   {result.algorithm==='committed-diff-with-prefix-aware-dependency-frontiers'&&<div className="apex-actions"><button className="secondary-button" disabled={busy||!token} onClick={()=>void recheckRepository()}>Recheck Git evidence</button>{verification&&<p role="status">{verification.status==='current'?'Current: the saved plan matches freshly derived Git evidence.':'Stale: references or saved plan evidence changed. Recompute before using it.'}</p>}</div>}
   <OptimizationResults result={result}/><dl className={styles.summary}>{summary.map(([key,value])=><div key={key}><dt>{key}</dt><dd>{text(value)}</dd></div>)}</dl>
   {tasks.length>0&&<div className={styles.graph}><h3>Dependency inspection</h3><p>Select a task to inspect its declared constraints. Arrows show prerequisites, not actual execution.</p><div className={styles.graphScroll}><svg viewBox={`0 0 810 ${Math.max(120,Math.ceil(graphTasks.length/4)*100+30)}`} role="img" aria-label="Declared task dependency graph; select a task using the buttons below"><defs><marker id="dependency-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#638d79"/></marker></defs>{graphTasks.flatMap(task=>(Array.isArray(task.dependencies)?task.dependencies:[]).map(parent=>{const from=locations.get(String(parent)),to=locations.get(String(task.id));return from&&to?<path key={`${parent}-${task.id}`} d={`M ${from.x+80} ${from.y+45} C ${from.x+80} ${from.y+85}, ${to.x+80} ${to.y-25}, ${to.x+80} ${to.y}`} fill="none" stroke={focus===task.id||focus===parent?'#245f40':'#a2bcae'} strokeWidth="2" markerEnd="url(#dependency-arrow)"/>:null;}))}{graphTasks.map(task=>{const point=locations.get(String(task.id))!;return <g key={String(task.id)}><rect x={point.x} y={point.y} width="160" height="45" rx="9" fill={focus===task.id?'#d8eedf':'#f1f7f3'} stroke="#6b957e"/><text x={point.x+80} y={point.y+28} textAnchor="middle" fontSize="12" fill="#234e38">{String(task.id).slice(0,20)}</text></g>;})}</svg></div>{tasks.length>64&&<p>Graph preview shows the first 64 tasks. The complete task directory and export remain available.</p>}<div className={styles.nodes}>{tasks.map(task=><button key={String(task.id)} aria-pressed={focus===task.id} onClick={()=>setFocus(String(task.id))}><strong>{String(task.id)}</strong><span>{Array.isArray(task.dependencies)&&task.dependencies.length?`${task.dependencies.join(' + ')} → ${task.id}`:'Ready without prerequisites'}</span></button>)}</div>{focused&&<pre className="apex-json">{JSON.stringify(focused,null,2)}</pre>}</div>}
   <details><summary>Full evidence and limitations</summary><pre className="apex-json">{JSON.stringify(result,null,2)}</pre></details>
  </section>}
 </>;
}
