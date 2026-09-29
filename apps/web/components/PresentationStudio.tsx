/**
 * React component for presentation studio.
 *
 * @module PresentationStudio
 * @packageDocumentation
 */
'use client';

import {useEffect, useMemo, useState} from 'react';
import {Download, FileUp, Presentation, Sparkles} from 'lucide-react';
import {parseSnapshot, type Snapshot} from '@/lib/graph';
import styles from './PresentationStudio.module.css';

/**
 * Type Audience.
 *
 *
 * @example
 * ```typescript
 * import { Audience } from './module';
 * ```
 */
type Audience = 'elevator'|'shark'|'vc'|'pe';
/**
 * Type QA.
 *
 *
 * @example
 * ```typescript
 * import { QA } from './module';
 * ```
 */
type QA = {question:string;answer:string;source?:string};
/**
 * Type Slide.
 *
 *
 * @example
 * ```typescript
 * import { Slide } from './module';
 * ```
 */
type Slide = {title:string;body:string;note:string};
const audiences:Record<Audience,{label:string;focus:string;length:string}> = {
  elevator:{label:'Elevator pitch',focus:'Clarity · urgency · memorable ask',length:'30–60 seconds'},
  shark:{label:'Shark Tank style',focus:'Customer proof · economics · direct ask',length:'5-minute pitch'},
  vc:{label:'VC investment committee',focus:'Venture scale · repeatability · returns path',length:'Investment memo + 10-slide outline'},
  pe:{label:'Private equity committee',focus:'Cash flow · diligence · operational value creation',length:'Deal committee brief + operating plan'},
};
const blank = 'Not supplied — add a sourced figure before presenting.';
/**
 * Function clean.
 *
 * @param {string} value - Description of value.
 * @param max - Description of max.
 *
 * @example
 * ```typescript
 * const result = clean(..., ...);
 * ```
 */
function clean(value:string,max=10000){return value.trim().slice(0,max);}
/**
 * Function parseQAs.
 *
 * @param {string} raw - Description of raw.
 * @returns {QA[]} Description of return value.
 *
 * @example
 * ```typescript
 * const result = parseQAs(...);
 * ```
 */
function parseQAs(raw:string):QA[]{
  const value:unknown=JSON.parse(raw);
  const items=Array.isArray(value)?value:(value&&typeof value==='object'&&Array.isArray((value as {items?:unknown}).items)?(value as {items:unknown[]}).items:[]);
  if(!items.length||items.length>200) throw new Error('Provide a JSON array (or {"items": [...]}) with 1–200 question/answer records.');
  return items.map((item,index)=>{
    if(!item||typeof item!=='object')throw new Error(`Q&A record ${index+1} must be an object.`);
    const row=item as Record<string,unknown>,question=typeof row.question==='string'?clean(row.question,2000):'',answer=typeof row.answer==='string'?clean(row.answer,4000):'';
    if(!question||!answer)throw new Error(`Q&A record ${index+1} needs non-empty question and answer fields.`);
    return {question,answer,...(typeof row.source==='string'?{source:clean(row.source,500)}:{})};
  });
}
/**
 * Function graphSummary.
 *
 * @param {Snapshot|null} graph - Description of graph.
 *
 * @example
 * ```typescript
 * const result = graphSummary(...);
 * ```
 */
function graphSummary(graph:Snapshot|null){
  if(!graph)return 'No graph attached. Import a Graph Studio JSON snapshot or use the prepared project snapshot.';
  const parsed=graph.nodes.filter(n=>n.confidence==='parsed').length,observed=graph.nodes.filter(n=>n.confidence==='observed').length,inferred=graph.nodes.filter(n=>n.confidence==='inferred').length;
  const leaders=[...graph.nodes].sort((a,b)=>(b.connections||0)-(a.connections||0)).slice(0,5).filter(n=>(n.connections||0)>0);
  return `${graph.name}: ${graph.nodes.length.toLocaleString()} nodes, ${graph.edges.length.toLocaleString()} relationships. Node evidence: ${parsed} parsed, ${observed} observed, ${inferred} inferred. ${graph.warnings.length} coverage warnings${graph.truncated?' · snapshot truncated':''}.`+(leaders.length?` High-connectivity symbols: ${leaders.map(n=>`${n.name} (${n.kind}, ${n.connections} connections, ${n.confidence})`).join('; ')}.`:'');
}
/**
 * Function createDraft.
 *
 * @param {Audience} audience - Description of audience.
 * @param {string} project - Description of project.
 * @param {string} description - Description of description.
 * @param {string} evidence - Description of evidence.
 * @param {string} economics - Description of economics.
 * @param {QA[]} qa - Description of qa.
 * @param {Snapshot|null} graph - Description of graph.
 *
 * @example
 * ```typescript
 * const result = createDraft(..., ..., ..., ..., ..., ..., ...);
 * ```
 */
function createDraft(audience:Audience,project:string,description:string,evidence:string,economics:string,qa:QA[],graph:Snapshot|null){
  const name=clean(project)||'Project name not supplied';
  const problem=clean(description)||'The specific customer problem and urgency have not been supplied.';
  const business=clean(evidence)||blank;
  const unit=clean(economics)||'Revenue, gross margin, acquisition cost, retention, payback and operating cost are not supplied.';
  const graphText=graphSummary(graph);
  const qaText=qa.length?qa.slice(0,12).map(item=>`Q: ${item.question}\nA: ${item.answer}${item.source?`\nSource: ${item.source}`:''}`).join('\n\n'):'No tracked Q&A records imported.';
  let pitch=''; let slides:Slide[]=[];
  if(audience==='elevator'){
    pitch=`${name} helps [specific customer] solve ${problem} through [distinct approach]. ${business} We are looking for [specific next step] from [target listener].`;
    slides=[{title:'One sentence',body:`${name}: [customer] gets [measurable outcome] by [how it works].`,note:'Replace bracketed fields with verified claims.'},{title:'Proof and ask',body:`Proof: ${business}\nAsk: [intro, pilot, hire, or meeting]`,note:'Keep under one minute. Lead with the listener’s most relevant outcome.'}];
  } else if(audience==='shark'){
    pitch=`We are ${name}. We serve [defined customer] who face ${problem}. Our product [how it works]. To date: ${business} Our business economics are: ${unit} We are asking for [amount or commercial commitment] in exchange for [specific terms/use of funds].`;
    slides=[{title:'The customer pain',body:problem,note:'Name who pays and how often this pain occurs; source every number.'},{title:'Product and why now',body:`${name} · [demo or workflow]`,note:'Show the product solving the problem in one concrete use case.'},{title:'Traction',body:business,note:'Use dated, attributable customer and usage evidence.'},{title:'Unit economics',body:unit,note:'State definitions, period, cohort and source for every figure.'},{title:'Competition and edge',body:'[Alternatives] · [switching reason] · [defensible advantage]',note:'Do not call an untested feature a moat.'},{title:'The ask',body:'[Investment] for [ownership/terms] to achieve [milestones].',note:'Validate valuation and terms before presenting.'}];
  } else if(audience==='vc'){
    pitch=`Investment thesis — ${name}: [why this can become a large, repeatable business]. Initial wedge: ${problem} Product and technical evidence: ${graphText} Commercial evidence: ${business} Economics and model: ${unit} Proposed financing and milestones: [round, use of funds, runway, measurable next proof].`;
    slides=[{title:'Thesis and decision requested',body:`${name} · [round / amount / instrument]\n[One-line venture-scale thesis]`,note:'State the exact committee decision requested.'},{title:'Problem, buyer and urgency',body:problem,note:'Quantify frequency, budget owner and current workaround with sourced evidence.'},{title:'Product and differentiated mechanism',body:`${name}\n${graphText}`,note:'Graph structure can explain implementation; it does not itself prove customer value or defensibility.'},{title:'Market and wedge',body:'[Bottom-up serviceable market] · [initial segment] · [expansion path]',note:'Separate sourced market data from management assumptions.'},{title:'Traction and retention',body:business,note:'Include cohort definitions, dates and retention/usage evidence.'},{title:'Business model and unit economics',body:unit,note:'Show gross margin, CAC, payback, LTV method and sensitivity only when evidenced.'},{title:'Competition and moat formation',body:'[Incumbents / substitutes] · [switching costs, data, distribution or scale evidence]',note:'Distinguish current advantage from a moat that may develop.'},{title:'Go-to-market and scaling constraints',body:'[Channel] · [sales cycle] · [implementation cost] · [capacity bottleneck]',note:'Show repeatability by cohort/channel.'},{title:'Risks and milestones',body:'[Top risks] · [mitigations] · [12–24 month proof points]',note:'Include technical, regulatory, concentration and execution risks.'},{title:'Team, financing and ask',body:'[Relevant founder proof] · [capital requested] · [runway] · [milestone-linked use]',note:'No terms, team credentials or runway were inferred.'}];
  } else {
    pitch=`Deal brief — ${name}. Investment case: [durable cash generation or operational improvement]. Business overview: ${problem} Evidence available: ${business} Technical operating map: ${graphText} Current unit economics: ${unit} Diligence and value-creation priorities: [validated actions, owner, cost, timing, downside case].`;
    slides=[{title:'Transaction overview and decision',body:'[Asset / transaction / proposed terms / committee decision]',note:'Do not imply verified deal facts that have not been supplied.'},{title:'Business quality and earnings durability',body:business,note:'Show recurring revenue, customer concentration, churn and cyclicality using primary records.'},{title:'Operating model and dependencies',body:graphText,note:'Repository graph evidence describes software structure; it does not establish process controls or operational performance.'},{title:'Cash conversion and downside case',body:unit,note:'Reconcile EBITDA to cash, working capital, capex and debt service.'},{title:'Diligence findings and open items',body:qaText,note:'Imported Q&A is user-provided context; label respondent, date and source before relying on it.'},{title:'Value-creation plan',body:'[Initiative] · [baseline KPI] · [owner] · [one-time cost] · [expected range] · [measurement date]',note:'Use scenario ranges with named assumptions; avoid unsupported synergies.'},{title:'Risks, mitigants and sensitivities',body:'[Commercial] · [operational] · [technology] · [regulatory] · [financing]',note:'Quantify impact and downside where evidence permits.'},{title:'Returns, financing and recommendation',body:'[Entry assumptions] · [leverage] · [exit scenarios] · [returns range] · [conditions]',note:'Returns are not calculated until terms and assumptions are supplied.'}];
  }
  slides.push({title:'Technical system and evidence boundary',body:graphText,note:'Repository graph structure supports the technical walkthrough. It is not evidence of product-market fit, security quality or a moat.'});
  if(qa.length) slides.push({title:audience==='pe'?'Management Q&A and diligence':'Audience Q&A and evidence',body:qaText,note:'Imported records are user-provided context. Confirm respondent, date and primary source before presenting answers as fact.'});
  return {pitch,slides,graphText,qaText};
}
/**
 * React component PresentationStudio.
 *
 *
 * @example
 * ```typescript
 * import { PresentationStudio } from './module';
 * ```
 */
export default function PresentationStudio(){
 const [audience,setAudience]=useState<Audience>('vc'),[project,setProject]=useState(''),[description,setDescription]=useState(''),[evidence,setEvidence]=useState(''),[economics,setEconomics]=useState(''),[qaText,setQaText]=useState(''),[qa,setQa]=useState<QA[]>([]),[graph,setGraph]=useState<Snapshot|null>(null),[graphName,setGraphName]=useState('No graph attached'),[error,setError]=useState(''),[notice,setNotice]=useState('');
 const draft=useMemo(()=>createDraft(audience,project,description,evidence,economics,qa,graph),[audience,project,description,evidence,economics,qa,graph]);
 const [editedPitch,setEditedPitch]=useState(''),[editedDeck,setEditedDeck]=useState('');
 useEffect(()=>{fetch('/repository-graph.json').then(response=>response.ok?response.json():null).then(raw=>{if(raw){const parsed=parseSnapshot(raw);setGraph(parsed);setGraphName('Prepared project snapshot');}}).catch(()=>{});},[]);
 useEffect(()=>{setEditedPitch(draft.pitch);setEditedDeck(draft.slides.map((slide,index)=>`## ${index+1}. ${slide.title}\n${slide.body}\n\nPresenter note: ${slide.note}`).join('\n\n'));},[draft]);
 function importGraph(file?:File){if(!file)return;setError('');const reader=new FileReader();reader.onload=()=>{try{const parsed=parseSnapshot(JSON.parse(String(reader.result)));setGraph(parsed);setGraphName(file.name);setNotice(`Imported ${parsed.name}: ${parsed.nodes.length} nodes and ${parsed.edges.length} edges.`);}catch(e){setError(e instanceof Error?e.message:'Could not read graph snapshot.');}};reader.onerror=()=>setError('Could not read selected graph file.');reader.readAsText(file);}
 function importQA(file?:File){if(!file)return;const reader=new FileReader();reader.onload=()=>{try{const records=parseQAs(String(reader.result));setQa(records);setQaText(JSON.stringify(records,null,2));setNotice(`Imported ${records.length} Q&A records. Add dates and sources before presenting sensitive claims.`);setError('');}catch(e){setError(e instanceof Error?e.message:'Could not read Q&A records.');}};reader.readAsText(file);}
 function loadQA(){try{const records=parseQAs(qaText);setQa(records);setNotice(`Loaded ${records.length} Q&A records into this draft.`);setError('');}catch(e){setError(e instanceof Error?e.message:'Invalid Q&A JSON.');}}
 function exportMarkdown(){const text=`# ${project||'Project presentation'} — ${audiences[audience].label}\n\n## Spoken pitch\n\n${editedPitch}\n\n## Presentation outline\n\n${editedDeck}\n\n## Evidence and limitations\n\n- Graph source: ${graphName}. ${draft.graphText}\n- Imported Q&A records: ${qa.length}. User-provided records; verify respondent, date and primary source.\n- No market size, customer traction, financial result, price, valuation, or moat is inferred by this draft.\n`;const url=URL.createObjectURL(new Blob([text],{type:'text/markdown'})),link=document.createElement('a');link.href=url;link.download=`${(project||'project').toLowerCase().replace(/[^a-z0-9]+/g,'-')}-${audience}-presentation.md`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
 async function copyPitch(){try{await navigator.clipboard.writeText(editedPitch);setNotice('Pitch copied to clipboard.');}catch{setNotice('Clipboard access is unavailable in this browser. Select and copy the pitch text.');}}
 return <div className={`page-content ${styles.page}`}><section className="page-heading"><div><span className="eyebrow">AUDIENCE-AWARE STORYTELLING · EVIDENCE-GROUNDED</span><h1>Presentation Studio<span> Make the case for this room.</span></h1><p>Turn project evidence, graph structure and tracked Q&A into a clear pitch or investment committee narrative.</p></div><button className="secondary-button" onClick={exportMarkdown}><Download size={15}/>Export presentation</button></section>
  <div className={styles.audienceGrid} role="group" aria-label="Choose presentation audience">{(Object.keys(audiences) as Audience[]).map(key=><button type="button" key={key} className={`${styles.audienceCard} ${audience===key?styles.selected:''}`} aria-pressed={audience===key} onClick={()=>setAudience(key)}><span>{audience===key?'SELECTED FORMAT':'AUDIENCE'}</span><strong>{audiences[key].label}</strong><small>{audiences[key].focus}</small></button>)}</div>
  <p className={styles.audienceHint}><Sparkles size={15}/>{audiences[audience].length} · optimized for {audiences[audience].focus.toLowerCase()}</p>
  <div className={styles.workspace}><section className={styles.inputs}><div className={styles.sectionHead}><span className="eyebrow">01 / SOURCES</span><h2>Ground the story</h2><p>Only claims supplied here or derived from the attached graph are included.</p></div>
   <label className={styles.field}>Project or company name<input value={project} onChange={e=>setProject(e.target.value)} maxLength={160} placeholder="e.g. ApexGraphSwarm"/></label>
   <label className={styles.field}>Customer problem and product description<textarea value={description} onChange={e=>setDescription(e.target.value)} rows={4} maxLength={4000} placeholder="Who has the problem, what hurts, and what does the project do?"/></label>
   <label className={styles.field}>Commercial proof and sourced evidence<textarea value={evidence} onChange={e=>setEvidence(e.target.value)} rows={4} maxLength={8000} placeholder="Customers, usage, pilots, retention, dated source links, team evidence. Leave unknowns blank."/></label>
   <label className={styles.field}>Unit economics and deal assumptions<textarea value={economics} onChange={e=>setEconomics(e.target.value)} rows={4} maxLength={8000} placeholder="Price, COGS, gross margin, CAC, payback, recurring revenue, capex, debt, valuation assumptions—with periods and sources."/></label>
   <div className={styles.importRow}><div><strong>Project graph</strong><small>{graphName} · {graph?`${graph.nodes.length.toLocaleString()} nodes / ${graph.edges.length.toLocaleString()} edges`: 'no graph loaded'}</small></div><label className={styles.fileButton}><FileUp size={15}/>Import graph JSON<input type="file" accept="application/json,.json" onChange={e=>importGraph(e.target.files?.[0])}/></label></div>
   <label className={styles.field}>Tracked Q&A records <small>Import records from your own log or paste JSON: [{`{ "question": "…", "answer": "…", "source": "…" }`}]. Decision Studio results are not read automatically.</small><textarea value={qaText} onChange={e=>setQaText(e.target.value)} rows={7} spellCheck={false} placeholder={'[\n  {"question":"What evidence supports adoption?","answer":"…","source":"interview log, 2026-09-01"}\n]'}/></label><div className={styles.rowActions}><label className={styles.fileButton}><FileUp size={15}/>Import Q&A JSON<input type="file" accept="application/json,.json" onChange={e=>importQA(e.target.files?.[0])}/></label><button className={styles.subtleButton} onClick={loadQA}>Use Q&A in draft</button><span>{qa.length} loaded record{qa.length===1?'':'s'}</span></div>
   {error&&<p role="alert" className={styles.error}>{error}</p>}{notice&&<p role="status" className={styles.notice}>{notice}</p>}
   <div className={styles.evidenceNote}><strong>Evidence boundary</strong><p>Graph structure can explain modules, relationships and coverage. It cannot prove product-market fit, market size, revenue, security quality or an economic moat. Unknown claims remain visibly open.</p></div>
  </section>
  <section className={styles.output}><div className={styles.sectionHead}><span className="eyebrow">02 / PRESENTATION</span><h2>{audiences[audience].label}</h2><p>{audiences[audience].focus}</p></div>
   <article className={styles.pitchCard}><div className={styles.cardTitle}><div><span className="eyebrow">SPOKEN VERSION</span><h3>{audiences[audience].length}</h3></div><button className={styles.subtleButton} onClick={()=>void copyPitch()}>Copy pitch</button></div><textarea aria-label="Editable spoken pitch" value={editedPitch} onChange={e=>setEditedPitch(e.target.value)} rows={audience==='elevator'?6:8}/></article>
   <article className={styles.pitchCard}><div className={styles.cardTitle}><div><span className="eyebrow">INVESTOR DECK / BRIEF</span><h3>Editable outline</h3></div><Presentation size={20}/></div><textarea aria-label="Editable presentation slides and presenter notes" value={editedDeck} onChange={e=>setEditedDeck(e.target.value)} rows={24}/></article>
   <article className={styles.graphCard}><span className="eyebrow">GRAPH EVIDENCE · {graphName.toUpperCase()}</span><p>{draft.graphText}</p>{graph?.warnings.length? <details><summary>Coverage warnings ({graph.warnings.length})</summary><ul>{graph.warnings.slice(0,10).map((warning,index)=><li key={`${index}-${warning}`}>{warning}</li>)}</ul></details>:null}</article>
   {qa.length>0&&<article className={styles.graphCard}><span className="eyebrow">TRACKED QUESTIONS & ANSWERS · {qa.length}</span>{qa.slice(0,8).map((item,index)=><details key={`${index}-${item.question}`}><summary>{item.question}</summary><p>{item.answer}</p>{item.source&&<small>Source: {item.source}</small>}</details>)}{qa.length>8&&<small>Showing first 8 records in preview; all imported records remain attached to pitch context.</small>}</article>}
   <div className={styles.reviewBanner}><strong>Before this reaches an investor</strong><p>Replace placeholders, verify each claim at source, date the evidence and review the ask, valuation, and financial assumptions with your advisors.</p></div>
  </section></div>
 </div>;
}
