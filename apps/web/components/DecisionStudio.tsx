/**
 * React component for decision studio.
 *
 * @module DecisionStudio
 * @packageDocumentation
 */
'use client';

import {useEffect, useMemo, useRef, useState} from 'react';
import type {DecisionAnswer, DecisionInput, DecisionProvider, DecisionQuestion, DecisionResult, ProviderInfo} from '@/lib/decision-types';
import {buildDecisionFixture} from '@/lib/decision-fixture';
import styles from './DecisionStudio.module.css';

/**
 * Type Context.
 *
 *
 * @example
 * ```typescript
 * import { Context } from './module';
 * ```
 */
type Context = 'graph'|'swarm'|'teams'|'analytics'|'optimization'|'delegation'|'evaluations'|'ecosystem'|'overview';
/**
 * Type Preset.
 *
 *
 * @example
 * ```typescript
 * import { Preset } from './module';
 * ```
 */
type Preset = {id:string;title:string;summary:string;questions:Record<string,DecisionQuestion>};

const presets:Record<Context,Preset> = {
 graph:{id:'graph',title:'Graph review',summary:'Compare possible next graph investigations using context you provide.',questions:{'next-step':{type:'choice',instructions:'Which graph investigation should be prioritized, and why?',criteria:['Inspect an uncertain dependency','Review a high-centrality module','Validate a cross-package edge']},'evidence-gap':{type:'noul',instructions:'Is the evidence sufficient to act on the selected graph finding? Answer yes or no.'}}},
 swarm:{id:'swarm',title:'Swarm routing',summary:'Assess a routing choice against explicit workload constraints.',questions:{'route':{type:'choice',instructions:'Which execution route best fits this task under the stated constraints?',criteria:['Local configured worker','Configured hosted integration','Defer until capacity is available']},'risk':{type:'score',instructions:'Score the operational risk from 0 (low) to 4 (high).',criteria:['0 = low risk','1 = limited risk','2 = moderate risk','3 = high risk','4 = unacceptable risk']}}},
 teams:{id:'teams',title:'Team coordination',summary:'Review ownership and coordination options from supplied context.',questions:{'coordination':{type:'choice',instructions:'Which coordination approach best addresses the stated dependencies?',criteria:['Single owner with reviewers','Parallel owners with explicit handoffs','Sequence work behind a shared dependency']},'ready':{type:'noul',instructions:'Are ownership and handoffs sufficiently explicit to start this plan? Answer yes or no.'}}},
 analytics:{id:'analytics',title:'Analytics interpretation',summary:'Interpret supplied metrics without treating association as causation.',questions:{'finding':{type:'choice',instructions:'Which interpretation is best supported by the supplied evidence?',criteria:['A descriptive difference is present','The evidence is inconclusive','A follow-up measurement is needed']},'causal-claim':{type:'noul',instructions:'Does the supplied evidence establish a causal effect? Answer yes or no.'}}},
 optimization:{id:'optimization',title:'Optimization review',summary:'Select a bounded optimization experiment from user-provided measurements.',questions:{'experiment':{type:'choice',instructions:'Which bounded experiment should be run next?',criteria:['Tune one configuration parameter','Collect a larger representative sample','Keep the current configuration']},'confidence':{type:'score',instructions:'Score confidence in the proposed experiment from 0 (low) to 4 (high).',criteria:['0 = very low','1 = low','2 = moderate','3 = high','4 = very high']}}},
 delegation:{id:'delegation',title:'Delegation review',summary:'Review task ownership and evidence requirements.',questions:{'delegate':{type:'choice',instructions:'Which task should be delegated first given the stated dependencies?',criteria:['The independent review task','The blocking implementation task','No delegation until inputs are clarified']},'ready':{type:'noul',instructions:'Is the delegated task sufficiently scoped and evidence-backed to begin? Answer yes or no.'}}},
 evaluations:{id:'evaluations',title:'Evaluation review',summary:'Assess evaluation evidence and identify a next step.',questions:{'decision':{type:'choice',instructions:'What is the most defensible evaluation outcome?',criteria:['Continue evaluation','Withhold promotion pending evidence','Accept the result within the stated scope']},'gate':{type:'noul',instructions:'Does the supplied evidence satisfy every stated evaluation gate? Answer yes or no.'}}},
 ecosystem:{id:'ecosystem',title:'Ecosystem review',summary:'Compare integration choices using only supplied capabilities and constraints.',questions:{'integration':{type:'choice',instructions:'Which integration path best matches the explicit constraints?',criteria:['Use an already configured integration','Keep the workflow local','Defer until a required capability is configured']},'configured':{type:'noul',instructions:'Is the required integration capability explicitly configured? Answer yes or no.'}}},
 overview:{id:'overview',title:'General decision',summary:'Frame a choice and a yes/no decision question.',questions:{'choice':{type:'choice',instructions:'Which option best satisfies the stated goal and constraints?',criteria:['Option A','Option B']},'ready':{type:'noul',instructions:'Is the supplied evidence sufficient to make this decision? Answer yes or no.'}}},
};

/**
 * Function usdToMicrousd.
 *
 * @param {string} raw - Description of raw.
 * @returns {number|null} Description of return value.
 *
 * @example
 * ```typescript
 * const result = usdToMicrousd(...);
 * ```
 */
function usdToMicrousd(raw:string):number|null {
 if(!/^\d{1,9}(?:\.\d{1,6})?$/.test(raw.trim()))return null;
 const value=Number(raw);if(!Number.isFinite(value)||value<0||value>1000000)return null;
 const micros=Math.round(value*1_000_000);return Number.isSafeInteger(micros)?micros:null;
}
/**
 * Function money.
 *
 * @param {number|null|undefined} value - Description of value.
 *
 * @example
 * ```typescript
 * const result = money(...);
 * ```
 */
function money(value:number|null|undefined){return value==null?'Unknown':`$${(value/1_000_000).toFixed(6)}`}
/**
 * Function typeLabel.
 *
 * @param {DecisionQuestion['type']} type - Description of type.
 *
 * @example
 * ```typescript
 * const result = typeLabel(...);
 * ```
 */
function typeLabel(type:DecisionQuestion['type']){return type==='noul'?'Yes/no decision · probability':'Structured choice/score decision';}
/**
 * Function criteriaText.
 *
 * @param {DecisionQuestion} question - Description of question.
 *
 * @example
 * ```typescript
 * const result = criteriaText(...);
 * ```
 */
function criteriaText(question:DecisionQuestion){return Array.isArray(question.criteria)?question.criteria.join('\n'):question.criteria?JSON.stringify(question.criteria,null,2):'';}
/**
 * Function parseCriteria.
 *
 * @param {string} text - Description of text.
 * @param {DecisionQuestion['type']} type - Description of type.
 * @returns {DecisionQuestion['criteria']|undefined} Description of return value.
 *
 * @example
 * ```typescript
 * const result = parseCriteria(..., ...);
 * ```
 */
function parseCriteria(text:string,type:DecisionQuestion['type']):DecisionQuestion['criteria']|undefined {
 if(type==='noul'||!text.trim())return undefined;
 if(type==='choice')return text.split('\n').map(row=>row.trim()).filter(Boolean);
 try{const parsed:unknown=JSON.parse(text);if(Array.isArray(parsed)&&parsed.every(item=>typeof item==='string'))return parsed;if(parsed&&typeof parsed==='object'&&!Array.isArray(parsed)&&Object.values(parsed).every(item=>typeof item==='string'))return parsed as Record<string,string>;}catch{}
 return text.split('\n').map(row=>row.trim()).filter(Boolean);
}
/**
 * React component DecisionStudio.
 *
 * @param {{context?} context='overview' - Description of context='overview'.
 *
 * @example
 * ```typescript
 * const result = DecisionStudio(...);
 * ```
 */
export default function DecisionStudio({context='overview'}:{context?:Context}) {
 const initial=presets[context]??presets.overview;
 const [state,setState]=useState('');
 const [questions,setQuestions]=useState<Record<string,DecisionQuestion>>(initial.questions);
 const [presetId,setPresetId]=useState(initial.id);
 const [providers,setProviders]=useState<ProviderInfo[]>([]);
 const [selectedProviders,setSelectedProviders]=useState<DecisionProvider[]>(['laya']);
 const [threshold,setThreshold]=useState(0.75),[thresholdAtRun,setThresholdAtRun]=useState(0.75),[budget,setBudget]=useState('0.10'),[token,setToken]=useState('');
 const [advanced,setAdvanced]=useState(false),[advancedText,setAdvancedText]=useState('');
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState(''),[results,setResults]=useState<DecisionResult[]|null>(null),[fixture,setFixture]=useState(false);
 const controller=useRef<AbortController|null>(null);
 const budgetMicros=usdToMicrousd(budget);
 const selectedInfo=useMemo(()=>providers.filter(item=>selectedProviders.includes(item.id)),[providers,selectedProviders]);
 const estimatedTotal=useMemo(()=>!selectedInfo.length||selectedInfo.map(item=>item.estimatedCostPerQuestionMicrousd).some(value=>value==null)?null:selectedInfo.reduce((sum,item)=>sum+(item.estimatedCostPerQuestionMicrousd??0)*Object.keys(questions).length,0),[selectedInfo,questions]);

 useEffect(()=>{let active=true;fetch('/api/decisions',{cache:'no-store'}).then(async response=>{if(!response.ok)throw Error('Provider configuration is unavailable.');const body=await response.json();if(!Array.isArray(body.providers))throw Error('Provider status response is invalid.');if(active)setProviders(body.providers as ProviderInfo[]);}).catch(()=>{if(active)setError('Provider configuration could not be loaded. Check that the local decision service is available.');});return()=>{active=false;controller.current?.abort();setToken('');};},[]);
 useEffect(()=>{if(!advanced)return;setAdvancedText(JSON.stringify(questions,null,2));},[advanced]);

 function loadPreset(id:Context){const next=presets[id]??presets.overview;setPresetId(next.id);setQuestions(next.questions);setAdvanced(false);setResults(null);setFixture(false);setError('');setNotice(`${next.title} question template loaded. Add the task context yourself; repository data is never attached automatically.`);}
 function updateQuestion(id:string,change:Partial<DecisionQuestion>){setQuestions(current=>({...current,[id]:{...current[id],...change}}));setResults(null);setFixture(false);setError('');}
 function updateType(id:string,type:DecisionQuestion['type']){updateQuestion(id,{type,criteria:type==='noul'?undefined:type==='choice'?['Option A','Option B']:['0 = low','1 = moderate','2 = high']});}
 function addQuestion(){if(Object.keys(questions).length>=8)return;let index=Object.keys(questions).length+1;while(questions[`question-${index}`])index++;setQuestions(current=>({...current,[`question-${index}`]:{type:'choice',instructions:'What should be considered?',criteria:['Option A','Option B']}}));setResults(null);}
 function acceptAdvanced(){try{const parsed:unknown=JSON.parse(advancedText);if(!parsed||Array.isArray(parsed)||typeof parsed!=='object'||Object.keys(parsed).length<1||Object.keys(parsed).length>8)throw Error('Questions must be an object containing 1–8 questions.');for(const [id,item] of Object.entries(parsed)){if(!/^[a-zA-Z0-9_-]{1,48}$/.test(id)||!item||typeof item!=='object'||Array.isArray(item))throw Error('Each question needs a short safe ID and a question object.');const q=item as DecisionQuestion;if(!['choice','score','noul'].includes(q.type)||typeof q.instructions!=='string'||!q.instructions.trim()||q.instructions.length>1000)throw Error('Each question needs a supported type and instructions of at most 1,000 characters.');if(q.criteria!==undefined&&!(Array.isArray(q.criteria)&&q.criteria.every(x=>typeof x==='string')||typeof q.criteria==='object'&&q.criteria!==null&&!Array.isArray(q.criteria)&&Object.values(q.criteria).every(x=>typeof x==='string')))throw Error('Question criteria must be a string array or string map.');if(q.type==='choice'&&(!Array.isArray(q.criteria)||q.criteria.length<2||q.criteria.length>12))throw Error('Choice questions require 2–12 options.');}setQuestions(parsed as Record<string,DecisionQuestion>);setAdvanced(false);setError('');setNotice('Validated advanced questions.');setResults(null);}catch(err){setError(err instanceof Error?err.message:'Invalid question JSON.');}}

 function runFixture(){setResults((['laya','anyjev'] as const).map(provider=>buildDecisionFixture(provider,questions,threshold)));setThresholdAtRun(threshold);setFixture(true);setError('');setNotice('Fixture comparison loaded. These example answers and probabilities are synthetic; no inference or provider request occurred.');}
 async function submit(){
  setError('');setNotice('');setResults(null);setFixture(false);
  if(!state.trim()){setError('Add the specific state or evidence you want considered. Nothing is inferred from the repository.');return;}
  if(state.length>16000){setError('Context is limited to 16,000 characters.');return;}
  if(advanced){setError('Apply or discard the advanced JSON edits before running.');return;}
  const qids=Object.keys(questions);if(qids.length<1||qids.length>8){setError('Provide 1–8 questions.');return;}
  for(const [id,q] of Object.entries(questions)){if(!/^[a-zA-Z0-9_-]{1,48}$/.test(id)||!q.instructions.trim()||q.instructions.length>1000){setError(`Question ${id} needs a valid ID and instructions up to 1,000 characters.`);return;}if(q.type==='choice'&&(!Array.isArray(q.criteria)||q.criteria.length<2||q.criteria.length>12)){setError(`Choice question ${id} needs 2–12 options.`);return;}}
  if(!selectedProviders.length){setError('Select at least one configured provider.');return;}
  const configured=providers.filter(item=>selectedProviders.includes(item.id)&&item.configured);if(configured.length!==selectedProviders.length){setError('One or more selected providers are not configured on this server.');return;}
  if(!token.trim()){setError('Enter the private workspace token to authorize this request. It remains in memory only.');return;}
  if(budgetMicros===null){setError('Enter a USD budget from $0 to $1,000,000 with at most six decimal places.');return;}
  if(estimatedTotal!==null&&estimatedTotal>budgetMicros){setError(`The conservative configured estimate (${money(estimatedTotal)}) exceeds this request budget. Increase the budget or reduce questions/providers.`);return;}
  if(estimatedTotal===null){setError('A selected provider has no known configured estimate. The request is withheld because its budget eligibility cannot be established.');return;}
  const input:DecisionInput={providers:selectedProviders,state:state.trim(),questions,threshold,maxCostMicrousd:budgetMicros};
  setThresholdAtRun(threshold);
  const request=new AbortController();controller.current=request;setBusy(true);
  try{const response=await fetch('/api/decisions',{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`},body:JSON.stringify(input),signal:request.signal});const body=await response.json();if(!response.ok)throw Error(body.error||'Decision request failed.');if(!Array.isArray(body.results))throw Error('The decision service returned an invalid response.');setResults(body.results as DecisionResult[]);setNotice('Response received. Confidence and probabilities are advisory signals for review, not an authorization or execution decision.');}
  catch(err){if(!request.signal.aborted)setError(err instanceof Error?err.message:'Decision service unavailable.');}
  finally{if(controller.current===request){controller.current=null;setBusy(false);}}
 }

 return <main className={styles.studio}>
  <section className={styles.intro}><div><span className="eyebrow">DECISION WORKSPACE / USER-SUPPLIED CONTEXT</span><h2>Make the question inspectable.</h2><p>Choice, score and yes/no probability questions all produce structured decision-support outputs. A yes/no probability is not an open-ended research answer. None of these outputs authorizes an action; review the supplied evidence and provider response.</p></div><span className={styles.badge}>NO AUTOMATIC REPOSITORY CONTEXT</span></section>

  <section className={styles.providers} aria-label="Provider status"><div className={styles.sectionTitle}><div><span className="eyebrow">SERVER CONFIGURATION</span><h3>Choose an inference route</h3></div><span className={styles.fine}>Configuration status only; no endpoint URLs or secrets are exposed.</span></div><div className={styles.providerGrid}>{(['laya','anyjev'] as const).map(id=>{const info=providers.find(item=>item.id===id);const checked=selectedProviders.includes(id);return <label key={id} className={`${styles.provider} ${checked?styles.selected:''}`}><input type="checkbox" checked={checked} disabled={!info?.configured||busy} onChange={e=>setSelectedProviders(current=>e.target.checked?[...current,id]:current.filter(value=>value!==id))}/><span><strong>{info?.label??(id==='laya'?'Laya':'AnyJev')}</strong><small>{info?.statusText??'Checking server configuration…'}</small><small>Configured estimate per question: {info?.estimatedCostPerQuestionMicrousd==null?'Unknown':`${money(info.estimatedCostPerQuestionMicrousd)} estimated`}</small></span><em>{info?.configured?'AVAILABLE':'UNAVAILABLE'}</em></label>;})}</div><p className={styles.fine}>Compare sends the same user-supplied state and question set to both configured providers. Provider requests may return estimates; actual invoice cost is not available here.</p></section>

  <div className={styles.layout}><section className={styles.composer}><div className={styles.sectionTitle}><div><span className="eyebrow">01 / FRAME</span><h3>Your context</h3></div><button className={styles.ghost} onClick={()=>loadPreset(context)}>Load {presets[context]?.title??'general'} questions</button></div><label className={styles.field}>Specific state, evidence and constraints<textarea value={state} onChange={e=>{setState(e.target.value);setResults(null);setFixture(false);setError('');}} maxLength={16000} rows={8} placeholder="Paste only the context you want analyzed. For example: the observed options, goals, constraints, evidence, and unknowns. This is sent only after you submit."/><small>{state.length.toLocaleString()} / 16,000 characters · not saved to browser storage</small></label>
    <div className={styles.presetRow}><span>Question template</span>{Object.entries(presets).map(([key,item])=><button key={key} aria-pressed={presetId===key} onClick={()=>loadPreset(key as Context)}>{item.title}</button>)}</div><p className={styles.presetSummary}>{presets[presetId as Context]?.summary}</p>
    <div className={styles.questionHeading}><div><span className="eyebrow">02 / ASK</span><h3>Questions</h3></div><div className={styles.questionActions}><button className={styles.ghost} onClick={()=>setAdvanced(value=>!value)}>{advanced?'Close JSON editor':'Advanced JSON'}</button><button className={styles.ghost} disabled={Object.keys(questions).length>=8||advanced} onClick={addQuestion}>+ Add question</button></div></div>
    {advanced?<div className={styles.advanced}><label className={styles.field}>Questions JSON<textarea value={advancedText} onChange={e=>{setAdvancedText(e.target.value);setError('');}} rows={15} spellCheck={false}/></label><p>Schema: question IDs map to {`{type, instructions, criteria?}`} . Choice criteria require 2–12 option strings. Score criteria may be a string list or label map. Noul is a binary yes/no question; its numeric value is the reported probability of Yes.</p><button className="primary-button" onClick={acceptAdvanced}>Validate and apply JSON</button></div>:<div className={styles.questions}>{Object.entries(questions).map(([id,q],index)=><article className={styles.question} key={id}><div className={styles.questionTop}><span className={styles.qIndex}>Q{index+1}</span><span className={styles.idDisplay}>ID · {id}</span><label className={styles.typeField}>Output type<select value={q.type} onChange={e=>updateType(id,e.target.value as DecisionQuestion['type'])}><option value="choice">Choice / decision</option><option value="score">Score / decision</option><option value="noul">Noul / yes-no probability</option></select></label><button className={styles.remove} aria-label={`Remove ${id}`} disabled={Object.keys(questions).length<=1} onClick={()=>{setQuestions(current=>Object.fromEntries(Object.entries(current).filter(([key])=>key!==id)));setResults(null);setError('');}}>Remove</button></div><label className={styles.field}>Question instructions<textarea value={q.instructions} onChange={e=>updateQuestion(id,{instructions:e.target.value})} rows={2} maxLength={1000}/></label>{q.type!=='noul'&&<label className={styles.field}>{q.type==='choice'?'Options (one per line)':'Score criteria (JSON list/map or one per line)'}<textarea value={criteriaText(q)} onChange={e=>updateQuestion(id,{criteria:parseCriteria(e.target.value,q.type)})} rows={q.type==='choice'?3:2} placeholder={q.type==='choice'?'Option A\nOption B':'0 = low\n2 = high'}/><small>{q.type==='choice'?'2–12 options required.':'Score output is an integer criterion index from zero through the final criterion.'}</small></label>}<span className={styles.typeHint}>{typeLabel(q.type)} · {q.type==='noul'?'Probability value means P(Yes), with Yes/No distribution.':'Confidence is a model-reported estimate, not calibrated certainty.'}</span></article>)}</div>}
    <div className={styles.limits}><label className={styles.field}>Review threshold <output>{Math.round(threshold*100)}%</output><input type="range" min="0" max="1" step="0.01" value={threshold} onChange={e=>setThreshold(Number(e.target.value))}/><small>Answers below this threshold should receive additional human review. The server reports reviewRequired; this threshold never authorizes a task.</small></label><label className={styles.field}>Maximum estimated request budget (USD)<input inputMode="decimal" value={budget} onChange={e=>setBudget(e.target.value)} placeholder="0.10"/><small>{budgetMicros==null?'Use up to six decimal places.':`${budgetMicros.toLocaleString()} integer micro-USD`}. Unknown estimates block submission; actual cost remains unknown.</small></label></div>
    <label className={styles.field}>Private workspace token<input type="password" autoComplete="off" value={token} onChange={e=>setToken(e.target.value)} placeholder="Required for provider requests · kept in memory only"/><small>The token is sent in the Authorization header and is not saved in localStorage/sessionStorage.</small></label>
    {error&&<p role="alert" className={styles.error}>{error}</p>}{notice&&<p role="status" className={styles.notice}>{notice}</p>}
    <div className={styles.submitRow}><div><strong>Estimated request total</strong><small>{estimatedTotal==null?'Unknown until all selected provider estimates are configured.':`${money(estimatedTotal)} estimated`} · budget {budgetMicros==null?'invalid':money(budgetMicros)}</small></div><button className="primary-button" disabled={busy||advanced||!providers.length} onClick={()=>void submit()}>{busy?'Waiting for providers…':selectedProviders.length>1?'Compare providers':'Run decision review'}</button><button className={styles.ghost} disabled={busy} onClick={runFixture}>Show synthetic fixture</button></div>
    <p className={styles.disclaimer}>Submitting may call the selected configured providers. No request is made by loading this page or changing the form. Context and token exist only in component memory until the page is closed.</p>
   </section>

   <aside className={styles.side}><div className={styles.sideCard}><span className="eyebrow">REVIEW GUIDE</span><h3>Decision probability ≠ research answer</h3><p><strong>Choice and score</strong> questions return structured decision support with per-option probabilities or a numeric score.</p><p><strong>Noul</strong> is a yes/no question. Its numeric value is the probability of Yes and its distribution reports Yes/No probabilities.</p><p>Use the threshold to flag extra review. Confidence is advisory; it is not a safety guarantee, approval, or execution authority.</p></div><div className={styles.sideCard}><span className="eyebrow">BOUNDARY</span><h3>Keep context explicit</h3><p>This workspace does not silently query the repository, graph, swarm, or analytics store. Load a question template, then paste the precise context you want providers to see.</p><a href="/graph#integrations">Explore the separate graph-grounded research review path →</a><p className={styles.fine}>That separate integration does not connect a database or configure automatic authorization.</p></div></aside></div>

  {results&&<section className={styles.results} aria-live="polite"><div className={styles.sectionTitle}><div><span className="eyebrow">03 / REVIEW</span><h3>{fixture?'Synthetic fixture comparison':'Provider responses'}</h3></div><span className={fixture?styles.fixtureBadge:styles.badge}>{fixture?'FIXTURE · NO INFERENCE':'REVIEW REQUIRED'}</span></div>{fixture&&<p className={styles.warning}>Illustrative static data only. No inference or provider request occurred; latency and cost comparisons are omitted.</p>}<p className={styles.warning}>These responses are advisory and do not execute tasks, change routing or authorize an action. Review the original context and verify important claims.</p><div className={styles.resultGrid}>{results.map((result,index)=><article className={styles.resultCard} key={`${result.provider}-${index}`}><header><div><span className="eyebrow">{result.provider==='laya'?'LAYA':'ANYJEV'}</span><h4>{result.status==='succeeded'?result.model??'Provider response':result.status==='unconfigured'?'Not configured':'Request failed'}</h4></div><span className={result.status==='succeeded'?styles.ok:styles.badge}>{result.status.toUpperCase()}</span></header>{!fixture&&<div className={styles.metrics}><div><small>Elapsed latency</small><strong>{result.elapsedMs.toLocaleString()} ms</strong></div><div><small>Estimated cost</small><strong>{money(result.estimatedCostMicrousd)}</strong></div><div><small>Actual cost</small><strong>{result.actualCostMicrousd==null?'Unknown':money(result.actualCostMicrousd)}</strong></div></div>}{result.error&&<p role="alert" className={styles.error}>{result.error}</p>}{result.warnings.map((warning,i)=><p className={styles.fine} key={i}>{warning}</p>)}<div className={styles.answers}>{result.answers.map(answer=><Answer key={answer.id} answer={answer} question={questions[answer.id]} threshold={thresholdAtRun}/>)}</div></article>)}</div></section>}
 </main>;
}

/**
 * Function Answer.
 *
 * @param {{answer} answer,question,threshold - Description of answer,question,threshold.
 *
 * @example
 * ```typescript
 * const result = Answer(...);
 * ```
 */
function Answer({answer,question,threshold}:{answer:DecisionAnswer;question?:DecisionQuestion;threshold:number}){
 const entries=Object.entries(answer.distribution??{}).map(([label,value])=>[answer.type==='noul'?(label==='true'?'Yes':label==='false'?'No':label):label,value] as const).sort((a,b)=>b[1]-a[1]);
 const yesProbability=answer.type==='noul'&&typeof answer.value==='number'&&Number.isFinite(answer.value)&&answer.value>=0&&answer.value<=1?answer.value:null;
 const scoreLabel=answer.type==='score'&&typeof answer.value==='number'&&Number.isInteger(answer.value)&&Array.isArray(question?.criteria)?question.criteria[answer.value]??null:null;
 const valueText=yesProbability!==null?`P(Yes) ${(yesProbability*100).toFixed(1)}% · more likely ${yesProbability>=0.5?'Yes':'No'}`:answer.type==='score'?`Score ${String(answer.value)}${scoreLabel?` · ${scoreLabel}`:''}`:String(answer.value);
 return <section className={styles.answer}><div className={styles.answerHeader}><div><span className="eyebrow">{answer.type==='noul'?'YES/NO PROBABILITY':answer.type==='score'?'SCORE DECISION':'CHOICE DECISION'}</span><h5>{answer.id}</h5></div><span className={answer.reviewRequired||answer.confidence<threshold?styles.review:styles.ok}>{answer.reviewRequired||answer.confidence<threshold?'REVIEW':'ADVISORY'}</span></div><p className={styles.answerValue}>{valueText}</p><div className={styles.confidence}><span>Reported confidence</span><strong>{Number.isFinite(answer.confidence)?`${(answer.confidence*100).toFixed(1)}%`:'Unknown'}</strong></div>{entries.length>0&&<div className={styles.distribution} aria-label="Reported answer distribution">{entries.slice(0,12).map(([label,value])=><div className={styles.distributionRow} key={label}><span title={label}>{label}</span><div><i style={{width:`${Math.max(0,Math.min(100,value*100))}%`}}/></div><strong>{Number.isFinite(value)?`${(value*100).toFixed(1)}%`:'Unknown'}</strong></div>)}</div>}</section>;
}
