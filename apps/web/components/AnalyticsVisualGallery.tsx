/**
 * React component for analytics visual gallery.
 *
 * @module AnalyticsVisualGallery
 * @packageDocumentation
 */
'use client';
import {useMemo,useRef,useState} from 'react';
import type {AnalyticsReport} from '@/lib/analytics-types';
import {decimal,dollars} from '@/lib/analytics-types';
import {downloadJSON} from '@/lib/graph';
import AnalyticsVisual from './AnalyticsVisual';
import ChartTooltip from './ChartTooltip';
import {buildVisualData,type VisualKind} from '@/lib/analytics-visuals';
import styles from './AnalyticsVisualGallery.module.css';
/**
 * Type ExtraKind.
 *
 *
 * @example
 * ```typescript
 * import { ExtraKind } from './module';
 * ```
 */
type ExtraKind='decomposition'|'narrative'|'map'|'key-influencers'|'scripted';
/**
 * Type Choice.
 *
 *
 * @example
 * ```typescript
 * import { Choice } from './module';
 * ```
 */
type Choice=VisualKind|ExtraKind;
const families:{label:string;items:[Choice,string][]}[]=[
 {label:'Compare',items:[['bar','Bar'],['column','Column'],['stacked-bar','Stacked bar'],['stacked-column','Stacked column'],['percent-bar','100% stacked bar'],['percent-column','100% stacked column']]},
 {label:'Composition',items:[['pie','Pie'],['donut','Donut'],['treemap','Treemap'],['waterfall','Waterfall'],['funnel','Funnel']]},
 {label:'Trends',items:[['line','Line'],['area','Area'],['stacked-area','Stacked area'],['combo','Line + column'],['ribbon','Ribbon']]},
 {label:'Performance & explanation',items:[['gauge','Gauge'],['kpi','KPI cards'],['decomposition','Decomposition'],['narrative','Data narrative']]},
 {label:'Detail & extensions',items:[['table','Table'],['matrix','Matrix'],['map','Geographic maps'],['key-influencers','Key influencers'],['scripted','R / Python / custom']]},
];
const attemptsOnly=new Set<Choice>(['stacked-bar','stacked-column','percent-bar','percent-column','stacked-area','combo']);
const temporal=new Set<Choice>(['line','area','stacked-area','combo','ribbon']);
const unsupported:Partial<Record<Choice,{title:string;detail:string}>>={
 ribbon:{title:'Requires category history',detail:'A ribbon chart needs category rankings across repeated time periods. This snapshot contains separate daily and cohort summaries, so their joint history cannot be reconstructed. Import support for daily category measures is required before a truthful ribbon chart can be rendered.'},
 map:{title:'Requires geographic fields',detail:'Map, filled-map and geographic heatmap visuals need latitude/longitude or verified region identifiers. Execution events currently contain no geography. A geospatial data contract and map provider must be configured before enabling these views.'},
 'key-influencers':{title:'Requires a fitted explanatory model',detail:'Key-influencer analysis requires a target outcome, row-level features, validation splits and model diagnostics. Aggregate correlations do not establish which factors drive an outcome. Use Statistics for the descriptive evidence available now.'},
 scripted:{title:'Requires an isolated execution adapter',detail:'R/Python scripts and third-party custom visuals can execute code. This gallery renders built-in React/SVG visuals; it does not execute uploaded scripts or load Power BI AppSource packages. A reviewed sandbox adapter is required for that capability.'},
};
/**
 * Function TileIcon.
 *
 * @param {{kind} kind - Description of kind.
 *
 * @example
 * ```typescript
 * const result = TileIcon(...);
 * ```
 */
function TileIcon({kind}:{kind:Choice}){const pie=['pie','donut'].includes(kind);return <svg viewBox="0 0 28 24" width="28" height="24" aria-hidden="true">{pie?<><circle cx="13" cy="12" r="9" fill="none" stroke="currentColor" strokeWidth={kind==='donut'?5:2}/><path d="M13 3V12H22" fill="none" stroke="currentColor" strokeWidth="2"/></>:['line','area','combo','ribbon','stacked-area'].includes(kind)?<><path d="M2 20L9 12L15 16L25 3" fill="none" stroke="currentColor" strokeWidth="2"/><path d="M2 2V22H27" fill="none" stroke="currentColor" opacity=".3"/></>:<><rect x="3" y="12" width="5" height="10" rx="1" fill="currentColor" opacity=".45"/><rect x="11" y="6" width="5" height="16" rx="1" fill="currentColor" opacity=".7"/><rect x="19" y="2" width="5" height="20" rx="1" fill="currentColor"/></>}</svg>;}
/**
 * Function downloadText.
 *
 * @param {string} name - Description of name.
 * @param {string} text - Description of text.
 * @param {string} type - Description of type.
 *
 * @example
 * ```typescript
 * const result = downloadText(..., ..., ...);
 * ```
 */
function downloadText(name:string,text:string,type:string){const url=URL.createObjectURL(new Blob([text],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
/**
 * React component AnalyticsVisualGallery.
 *
 * @param {{report} report - Description of report.
 *
 * @example
 * ```typescript
 * const result = AnalyticsVisualGallery(...);
 * ```
 */
export default function AnalyticsVisualGallery({report}:{report:AnalyticsReport}){
 const [kind,setKind]=useState<Choice>('pie'),[dimension,setDimension]=useState<'tool'|'resource'|'day'>('tool');
 const [metric,setMetric]=useState<'attempts'|'succeeded'|'knownCostMicrousd'>('attempts'),[query,setQuery]=useState(''),[limit,setLimit]=useState(12),[selected,setSelected]=useState<string|null>(null),[target,setTarget]=useState('');
 const [notice,setNotice]=useState('');const chartRef=useRef<HTMLDivElement>(null);
 const data=useMemo(()=>buildVisualData(report,dimension,metric,limit,query),[report,dimension,metric,limit,query]);
 const filteredScopeTotal=useMemo(()=>{
  const needle=query.trim().toLocaleLowerCase('en-US');let total=0;
  const add=(value:number)=>{const next=total+value;if(!Number.isSafeInteger(next))return false;total=next;return true;};
  if(dimension==='day'){
   for(const row of report.daily){if(!needle||row.date.toLocaleLowerCase('en-US').includes(needle)){if(!add(row[metric]))return undefined;}}
  }else{
   for(const row of report.cohorts){const label=dimension==='tool'?row.tool:row.resource;if(!needle||label.toLocaleLowerCase('en-US').includes(needle)){if(!add(row[metric]))return undefined;}}
  }
  return total;
 },[report,dimension,metric,query]);
 const label=families.flatMap(f=>f.items).find(item=>item[0]===kind)?.[1]||kind;
 const valueLabel=(value:number)=>metric==='knownCostMicrousd'?dollars(value):decimal(value);
 const shareLabel=(value:number,denominator:number|undefined)=>denominator===undefined?'Not supplied':denominator===0?'Not defined (denominator 0)':`${(100*value/denominator).toFixed(1)}% (${decimal(value)} / ${decimal(denominator)})`;
 const selectedRow=data.rows.find(row=>row.id===selected),blocked=unsupported[kind];
 const targetNumber=target.trim()&&Number.isFinite(Number(target))&&Number(target)>0&&Number(target)<=Number.MAX_SAFE_INTEGER?Number(target):undefined;
 function choose(value:Choice){setKind(value);setSelected(null);setNotice('');if(temporal.has(value))setDimension('day');if(value==='decomposition'||value==='matrix')setDimension('tool');if(attemptsOnly.has(value))setMetric('attempts');}
 function select(id:string){setSelected(current=>current===id?null:id);}
 function exportSVG(){const svg=chartRef.current?.querySelector('svg');if(!svg){setNotice('This visual has no SVG image. Export its data instead.');return;}const copy=svg.cloneNode(true) as SVGElement;copy.setAttribute('xmlns','http://www.w3.org/2000/svg');downloadText(`apex-${kind}.svg`,new XMLSerializer().serializeToString(copy),'image/svg+xml');setNotice('SVG exported with its selected chart data.');}
 const byTool=useMemo(()=>{const groups=new Map<string,typeof report.cohorts>();for(const row of report.cohorts){const group=groups.get(row.tool)||[];group.push(row);groups.set(row.tool,group);}return [...groups].filter(([tool,rows])=>tool.toLowerCase().includes(query.toLowerCase()));},[report,query]);
 const displayedTools=data.rows.map(row=>row.label), displayedGroups=displayedTools.flatMap(tool=>{const found=byTool.find(([label])=>label===tool);return found?[found]:[];}), allMatrixResources=[...new Set(displayedGroups.flatMap(([,rows])=>rows.map(row=>row.resource)))].sort(), matrixResources=allMatrixResources.slice(0,20), matrixResourcesOmitted=allMatrixResources.length-matrixResources.length;
 const provenanceDetails=[{label:'Source',value:report.source==='demo'?'Synthetic demo':'Recorded or imported snapshot'},{label:'Generated at',value:report.generatedAt},{label:'Evidence completeness',value:data.partial?'Partial or unresolved evidence; see quality warning.':'As represented by this snapshot.'}];
 const cohortDetails=(rows:typeof report.cohorts,title:string)=>{
  const attempts=rows.reduce((sum,row)=>sum+row.attempts,0),succeeded=rows.reduce((sum,row)=>sum+row.succeeded,0),knownCost=rows.reduce((sum,row)=>sum+row.knownCostMicrousd,0),unresolved=rows.reduce((sum,row)=>sum+row.unknownCostRows,0),value=rows.reduce((sum,row)=>sum+row[metric],0);
  return {title,value,details:[{label:metric==='knownCostMicrousd'?'Known-cost subtotal':'Selected measure',value:valueLabel(value)},{label:'Attempts',value:decimal(attempts)},{label:'Succeeded',value:decimal(succeeded)},{label:'Other outcomes',value:decimal(attempts-succeeded)},{label:'Known cost',value:dollars(knownCost)},{label:'Unresolved cost rows',value:decimal(unresolved)},...provenanceDetails]};
 };
 const matrixDisplayTotal=displayedGroups.reduce((toolSum,[,rows])=>toolSum+rows.filter(row=>matrixResources.includes(row.resource)).reduce((resourceSum,row)=>resourceSum+row[metric],0),0);
 return <section className={styles.gallery} aria-label="Visualization gallery"><header className={styles.header}><div><span className="eyebrow">VISUALIZATION GALLERY</span><h2>Choose how the evidence speaks.</h2><p>Chart families inspired by familiar BI workflows. Each view uses the loaded snapshot and exposes its data requirements.</p></div><span className={styles.source}>{report.source==='demo'?'Synthetic dataset':'Recorded / imported snapshot'}</span></header>
 <div className={styles.layout}><aside className={styles.catalog} aria-label="Chart type selection">{families.map(family=><section key={family.label}><h3>{family.label}</h3><div>{family.items.map(([id,name])=><button key={id} aria-pressed={kind===id} onClick={()=>choose(id)} title={unsupported[id]?`${name}: additional data or adapter required`:name}><TileIcon kind={id}/><span>{name}</span>{unsupported[id]&&<small>Requires setup</small>}</button>)}</div></section>)}</aside>
 <div className={styles.workspace}><div className={styles.fields}><label>Group by<select value={dimension} disabled={temporal.has(kind)||(kind==='decomposition'||kind==='matrix')||Boolean(blocked)} onChange={event=>{setDimension(event.target.value as typeof dimension);setSelected(null);}}><option value="tool">Tool</option><option value="resource">Resource</option><option value="day">UTC day</option></select></label><label>Measure<select value={metric} disabled={attemptsOnly.has(kind)||Boolean(blocked)} onChange={event=>{setMetric(event.target.value as typeof metric);setSelected(null);}}><option value="attempts">Attempts</option><option value="succeeded">Succeeded attempts</option><option value="knownCostMicrousd">Known cost (USD)</option></select></label><label>Category slicer<input aria-label="Category slicer" value={query} onChange={event=>{setQuery(event.target.value);setSelected(null);}} placeholder="Filter category names"/></label><label>Visible categories<select value={limit} onChange={event=>setLimit(Number(event.target.value))}><option value={6}>6</option><option value={12}>12</option><option value={20}>20</option></select></label>{kind==='gauge'&&<label>Explicit target ({metric==='knownCostMicrousd'?'micro-USD':'count'})<input type="number" min="1" value={target} onChange={event=>setTarget(event.target.value)} placeholder="Set your target"/></label>}</div>
 <div className={styles.chartCard}><div className={styles.chartHeading}><div><h3>{label}</h3><p>{kind==='decomposition'?'Tool → resource hierarchy':`${dimension==='day'?'UTC day':dimension} · ${metric==='knownCostMicrousd'?'known recorded cost':metric}`}</p></div><strong>{valueLabel(data.totalValue)}<small>selected categories total</small></strong></div>
 {data.partial&&<p className={styles.warning}>The source cohort data is capped or incomplete. Totals and proportions describe the returned selection.</p>}{metric==='knownCostMicrousd'&&report.quality.unknownCostRows>0&&<p className={styles.warning}>Unknown costs are excluded from these known-cost amounts; this is not total spend.</p>}
 {data.omitted>0&&<p className={styles.note}>{data.omitted} matching categories omitted by the display limit. Increase the limit or narrow the slicer; percentages use displayed values only.</p>}
 {kind==='matrix'&&matrixResourcesOmitted>0&&<p className={styles.note}>{matrixResourcesOmitted} resources are omitted from the matrix columns. The selected-tools total above can include them; visible cells show {valueLabel(matrixDisplayTotal)} across the {matrixResources.length} displayed resource columns.</p>}
 {attemptsOnly.has(kind)&&<p className={styles.note}>Success versus other attempts. “Other” includes failures, open attempts and unknown outcomes; it is not a failure rate.</p>}
 {kind==='waterfall'&&<p className={styles.note}>Cumulative contributions of the displayed categories; no inferred profit, loss or period-over-period change.</p>}
 {kind==='funnel'&&<p className={styles.note}>Ranked category distribution in a funnel shape. These categories are not sequential conversion stages.</p>}
 <div ref={chartRef} className={styles.visual}>{blocked?<div className={styles.requirement}><h4>{blocked.title}</h4><p>{blocked.detail}</p><a href="https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualizations-overview" target="_blank" rel="noreferrer">Microsoft’s visualization overview ↗</a></div>:kind==='decomposition'?<div className={styles.tree}>{displayedGroups.map(([tool,rows])=><details key={tool} open><summary><ChartTooltip title={`${tool} tool subtotal`} details={[{label:'Selected measure',value:valueLabel(rows.reduce((sum,row)=>sum+row[metric],0))},{label:'Share of displayed total',value:shareLabel(rows.reduce((sum,row)=>sum+row[metric],0),data.totalValue)},{label:'Share of filtered scope',value:shareLabel(rows.reduce((sum,row)=>sum+row[metric],0),filteredScopeTotal)},{label:'Attempts',value:decimal(rows.reduce((sum,row)=>sum+row.attempts,0))},{label:'Succeeded',value:decimal(rows.reduce((sum,row)=>sum+row.succeeded,0))},{label:'Known cost',value:dollars(rows.reduce((sum,row)=>sum+row.knownCostMicrousd,0))},{label:'Unresolved cost rows',value:decimal(rows.reduce((sum,row)=>sum+row.unknownCostRows,0))},...provenanceDetails]}><span aria-label={`${tool}: ${valueLabel(rows.reduce((sum,row)=>sum+row[metric],0))} ${metric==='knownCostMicrousd'?'known cost USD':metric}`}>{tool} · {valueLabel(rows.reduce((sum,row)=>sum+row[metric],0))}</span></ChartTooltip></summary>{rows.map((row,index)=><p key={index}><ChartTooltip title={`${tool} → ${row.resource}`} details={[{label:'Selected measure',value:valueLabel(row[metric])},{label:'Attempts',value:decimal(row.attempts)},{label:'Succeeded',value:decimal(row.succeeded)},{label:'Other outcomes',value:decimal(row.attempts-row.succeeded)},{label:'Known cost',value:dollars(row.knownCostMicrousd)},{label:'Unresolved cost rows',value:decimal(row.unknownCostRows)},...provenanceDetails]}><span aria-label={`${tool} to ${row.resource}: ${valueLabel(row[metric])} ${metric==='knownCostMicrousd'?'known cost USD':metric}, ${row.attempts} attempts`}>{row.resource}</span></ChartTooltip><strong>{valueLabel(row[metric])}</strong></p>)}</details>)}{!displayedGroups.length&&<p>No matching hierarchy nodes.</p>}</div>:kind==='matrix'?<div className={styles.tableWrap}><table><caption>Tool × resource pivot · maximum 20 resource columns · missing cells have no recorded attempts</caption><thead><tr><th>Tool</th>{matrixResources.map(resource=><th key={resource}>{resource}</th>)}</tr></thead><tbody>{displayedGroups.map(([tool,rows])=><tr key={tool}><th>{tool}</th>{matrixResources.map(resource=>{const cells=rows.filter(row=>row.resource===resource);if(!cells.length)return <td key={resource}>—</td>;const value=cells.reduce((sum,row)=>sum+row[metric],0);return <td key={resource}><ChartTooltip title={`${tool} → ${resource}`} details={[{label:'Selected measure',value:valueLabel(value)},{label:'Attempts',value:decimal(cells.reduce((sum,row)=>sum+row.attempts,0))},{label:'Succeeded',value:decimal(cells.reduce((sum,row)=>sum+row.succeeded,0))},{label:'Other outcomes',value:decimal(cells.reduce((sum,row)=>sum+row.attempts-row.succeeded,0))},{label:'Known cost',value:dollars(cells.reduce((sum,row)=>sum+row.knownCostMicrousd,0))},{label:'Unresolved cost rows',value:decimal(cells.reduce((sum,row)=>sum+row.unknownCostRows,0))},...provenanceDetails]}><span aria-label={`${tool} to ${resource}: ${valueLabel(value)} ${metric==='knownCostMicrousd'?'known cost USD':metric}, ${cells.reduce((sum,row)=>sum+row.attempts,0)} attempts`}>{valueLabel(value)}</span></ChartTooltip></td>;})}</tr>)}</tbody></table></div>:kind==='narrative'?<div className={styles.narrative}><h4>Snapshot summary</h4><p>{report.kpis.attempts.toLocaleString()} attempts in the full snapshot include {report.kpis.succeeded.toLocaleString()} successful outcomes. Known recorded costs are {dollars(report.kpis.knownCostMicrousd)}; {report.quality.unknownCostRows.toLocaleString()} attempt costs remain unresolved.</p><p>The displayed category selection accounts for {valueLabel(data.totalValue)} across {data.rows.length} categories. {data.omitted?`${data.omitted} additional matching categories are omitted.`:''}</p><p>This summary is computed from supplied aggregates. It does not infer causes or generate a recommendation.</p></div>:<AnalyticsVisual compact kind={kind as VisualKind} rows={data.rows} metric={metric} onSelect={select} selected={selected} target={targetNumber} partial={data.partial} omitted={data.omitted} totalValue={data.totalValue} filteredTotalValue={filteredScopeTotal}/>}</div>
 {selectedRow&&<div className={styles.selection} role="status"><strong>{selectedRow.label}</strong><span>{valueLabel(selectedRow.value)} · {selectedRow.attempts} attempts · {selectedRow.succeeded} successes</span><button onClick={()=>setSelected(null)}>Clear selection</button></div>}
 <div className={styles.actions}><button className="secondary-button" disabled={Boolean(blocked)} onClick={exportSVG}>Export SVG</button><button className="secondary-button" onClick={()=>downloadJSON('apex-visual-evidence.json',{version:1,chart:kind,source:report.source,generatedAt:report.generatedAt,dimension,metric,query,limit,target:targetNumber??null,...data,limitations:report.limitations})}>Export chart evidence</button></div>{notice&&<p role="status">{notice}</p>}
 <details><summary>Underlying chart values</summary><div className={styles.tableWrap}><table><caption>Displayed selection; shares use its sum. Filtered-scope total before display limits: {filteredScopeTotal===undefined?'not safely representable':valueLabel(filteredScopeTotal)}.</caption><thead><tr><th>Category</th><th>Measure</th><th>Displayed share</th><th>Attempts</th><th>Succeeded</th></tr></thead><tbody>{data.rows.map(row=><tr key={row.id}><td><button onClick={()=>select(row.id)} aria-pressed={selected===row.id}>{row.label}</button></td><td>{valueLabel(row.value)}</td><td>{shareLabel(row.value,data.totalValue)}</td><td>{row.attempts}</td><td>{row.succeeded}</td></tr>)}</tbody></table></div></details></div>
 <p className={styles.note}>Scatter plots, histograms and heatmaps remain in Statistics. Forecast intervals remain in Predictions. This is a native visualization gallery, not Microsoft Power BI or an AppSource runtime.</p>
 </div></div></section>;
}
