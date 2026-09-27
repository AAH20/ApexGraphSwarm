'use client';
import {useId,type ReactNode} from 'react';
import {dollars} from '@/lib/analytics-types';
import {pieSegments,type AnalyticsMetric,type ChartDatum,type VisualKind,visualSupport} from '@/lib/analytics-visuals';
import styles from './AnalyticsVisual.module.css';

export type AnalyticsVisualProps={kind:VisualKind;rows:ChartDatum[];metric:AnalyticsMetric;onSelect?:(id:string)=>void;selected?:string|null;target?:number;partial?:boolean;omitted?:number;totalValue?:number;compact?:boolean};
const colors=['#276e68','#4b7fa5','#bc7732','#785c9c','#4d8060','#ae5360','#52737e','#a98a25','#6875a7','#875f48','#397f91','#9d5e8d','#568047','#ba684e','#4d6d9d','#9e8233','#477d7a','#8c5d5d','#6a7180','#a56637'];
const metricName=(metric:AnalyticsMetric)=>metric==='knownCostMicrousd'?'known recorded cost':metric==='succeeded'?'successful attempts':'attempts';
const format=(value:number,metric:AnalyticsMetric)=>metric==='knownCostMicrousd'?dollars(value):new Intl.NumberFormat('en-US',{maximumFractionDigits:0}).format(value);
const polar=(cx:number,cy:number,r:number,angle:number)=>({x:cx+r*Math.cos(angle*Math.PI/180),y:cy+r*Math.sin(angle*Math.PI/180)});
function arcPath(cx:number,cy:number,r:number,start:number,end:number):string{
 const first=polar(cx,cy,r,start),last=polar(cx,cy,r,end),large=Math.abs(end-start)>180?1:0;
 return `M ${first.x} ${first.y} A ${r} ${r} 0 ${large} 1 ${last.x} ${last.y}`;
}
function piePath(segment:{startAngle:number;endAngle:number},radius:number,inner:number):string{
 const start=polar(150,135,radius,segment.startAngle),end=polar(150,135,radius,segment.endAngle);
 const outerLarge=segment.endAngle-segment.startAngle>180?1:0;
 if(inner<=0)return `M 150 135 L ${start.x} ${start.y} A ${radius} ${radius} 0 ${outerLarge} 1 ${end.x} ${end.y} Z`;
 const innerEnd=polar(150,135,inner,segment.endAngle),innerStart=polar(150,135,inner,segment.startAngle);
 return `M ${start.x} ${start.y} A ${radius} ${radius} 0 ${outerLarge} 1 ${end.x} ${end.y} L ${innerEnd.x} ${innerEnd.y} A ${inner} ${inner} 0 ${outerLarge} 0 ${innerStart.x} ${innerStart.y} Z`;
}
function total(rows:ChartDatum[]):number{return rows.reduce((sum,row)=>sum+row.value,0);}
function chartRows(rows:ChartDatum[]):string|null{
 if(!Array.isArray(rows)||rows.length>20)return 'Select at most 20 categories to draw this chart.';
 const ids=new Set<string>();
 for(const row of rows){
  if(!row||typeof row.id!=='string'||!row.id||ids.has(row.id)||typeof row.label!=='string'||!row.label)return 'Chart categories must have unique, nonempty IDs and labels.';
  ids.add(row.id);
  if(!Number.isSafeInteger(row.value)||row.value<0||!Number.isSafeInteger(row.attempts)||row.attempts<0||!Number.isSafeInteger(row.succeeded)||row.succeeded<0||row.succeeded>row.attempts)return 'Chart values must be non-negative safe integers with successes no greater than attempts.';
 }
 return null;
}
function Table({rows,metric,totalValue,selected,onSelect,matrix=false}:{rows:ChartDatum[];metric:AnalyticsMetric;totalValue:number;selected?:string|null;onSelect?:(id:string)=>void;matrix?:boolean}){
 return <div className={styles.tableWrap}><table><caption>{matrix?'Category metric matrix':'Exact category values'}</caption><thead><tr><th scope="col">Category</th><th scope="col">{metricName(metric)}</th>{matrix&&<><th scope="col">Attempts</th><th scope="col">Succeeded</th><th scope="col">Share of selection</th></>}</tr></thead><tbody>{rows.map(row=><tr key={row.id}><th scope="row">{onSelect?<button type="button" className={styles.select} aria-pressed={selected===row.id} onClick={()=>onSelect(row.id)}>{row.label}</button>:row.label}</th><td>{format(row.value,metric)}</td>{matrix&&<><td>{row.attempts}</td><td>{row.succeeded}</td><td>{totalValue>0?`${(100*row.value/totalValue).toFixed(1)}%`:'No selected value'}</td></>}</tr>)}</tbody></table></div>;
}
function Segmented({rows,metric,kind}:{rows:ChartDatum[];metric:AnalyticsMetric;kind:VisualKind}){
 const horizontal=kind.endsWith('bar'),percent=kind.startsWith('percent-'),stacked=kind.startsWith('stacked-')||percent;
 const viewWidth=horizontal?760:Math.max(440,rows.length*56+90),viewHeight=horizontal?Math.max(170,rows.length*42+70):300;
 const max=Math.max(1,...rows.map(row=>percent?row.attempts:row.value));
 return <svg className={styles.svg} viewBox={`0 0 ${viewWidth} ${viewHeight}`} role="img" aria-label={`${kind} chart of ${metricName(metric)} by category`}>
  <title>{`${kind.replaceAll('-',' ')} chart: ${metricName(metric)} by category`}</title>
  <desc>{percent?'Each bar is an attempt cohort divided into succeeded and other attempts.':stacked?'Bars split attempts into succeeded and other attempts.':'Bar lengths are proportional to the selected recorded metric.'}</desc>
  {rows.map((row,index)=>{
   if(horizontal){
    const y=35+index*42,labelX=8,barX=175,barWidth=550,rowHeight=22;
    const denominator=percent?row.attempts:max;
    const full=percent?barWidth:(denominator?barWidth*row.value/max:0);
    const success=stacked&&denominator?full*(row.succeeded/denominator):full;
  return <g key={row.id} className={styles.mark}><text x={labelX} y={y+16}>{short(row.label)}</text><rect x={barX} y={y} width={barWidth} height={rowHeight} rx="4" fill="#e8eef0"/>{success>0&&<rect x={barX} y={y} width={success} height={rowHeight} rx="4" fill={colors[index%colors.length]}/>}{stacked&&full-success>0&&<rect x={barX+success} y={y} width={full-success} height={rowHeight} fill="#bdc8cc"/>}<text x={barX+barWidth+8} y={y+16}>{percent?`${row.attempts?Math.round(row.succeeded/row.attempts*100):0}%`:format(row.value,metric)}</text></g>;
   }
   const x=45+index*(viewWidth-90)/Math.max(1,rows.length),base=viewHeight-45,chartHeight=190,slot=(viewWidth-90)/Math.max(1,rows.length),barWidth=Math.max(5,Math.min(32,slot*.62));
   const denominator=percent?row.attempts:max;
   const full=percent?chartHeight:(denominator?chartHeight*row.value/max:0);
   const success=stacked&&denominator?full*(row.succeeded/denominator):full;
   return <g key={row.id} className={styles.mark}><rect x={x-barWidth/2} y={base-chartHeight} width={barWidth} height={chartHeight} fill="#edf1f2" rx="3"/>{success>0&&<rect x={x-barWidth/2} y={base-success} width={barWidth} height={success} fill={colors[index%colors.length]} rx="3"/>}{stacked&&full-success>0&&<rect x={x-barWidth/2} y={base-full} width={barWidth} height={full-success} fill="#bdc8cc"/>}<text x={x} y={base+15} textAnchor="middle">{short(row.label,10)}</text><text x={x} y={base-chartHeight-8} textAnchor="middle">{percent?`${row.attempts?Math.round(row.succeeded/row.attempts*100):0}%`:format(row.value,metric)}</text></g>;
  })}
  {stacked&&<g className={styles.legend}><rect x="12" y={viewHeight-17} width="9" height="9" fill="#276e68"/><text x="26" y={viewHeight-9}>Succeeded</text><rect x="105" y={viewHeight-17} width="9" height="9" fill="#bdc8cc"/><text x="119" y={viewHeight-9}>Other attempts</text></g>}
 </svg>;
}
function short(label:string,max=16){return label.length>max?`${label.slice(0,max-1)}…`:label;}

export default function AnalyticsVisual({kind,rows,metric,onSelect,selected,target,partial=false,omitted=0,totalValue,compact=false}:AnalyticsVisualProps){
 const id=useId(),titleId=`${id}-title`,descriptionId=`${id}-description`,invalid=chartRows(rows),visual=visualSupport(kind);
 const allTotal=totalValue??total(rows),frameClass=`${styles.root} ${compact?styles.compact:''}`;
 if(!visual.supported)return <section className={frameClass} aria-labelledby={titleId}><h3 id={titleId} className={compact?styles.visuallyHidden:''}>{kind.replaceAll('-',' ')}</h3><p role="status">{visual.reason}</p></section>;
 if(invalid)return <section className={frameClass} aria-labelledby={titleId}><h3 id={titleId} className={compact?styles.visuallyHidden:''}>{kind.replaceAll('-',' ')}</h3><p role="status">{invalid}</p></section>;
 if(!rows.length)return <section className={frameClass} aria-labelledby={titleId}><h3 id={titleId} className={compact?styles.visuallyHidden:''}>{kind.replaceAll('-',' ')}</h3><p role="status">No matching categories to display.</p></section>;
 if(['stacked-bar','stacked-column','percent-bar','percent-column','stacked-area','combo'].includes(kind)&&metric!=='attempts')return <section className={frameClass} aria-labelledby={titleId}><h3 id={titleId} className={compact?styles.visuallyHidden:''}>{kind.replaceAll('-',' ')}</h3><p role="status">This view needs attempt counts so successes and other attempts use a real denominator.</p></section>;
 const rowsTotal=total(rows),max=Math.max(1,...rows.map(row=>row.value));
 let content:ReactNode;
 if(kind==='table'||kind==='matrix')content=<Table rows={rows} metric={metric} totalValue={allTotal} selected={selected} onSelect={onSelect} matrix={kind==='matrix'}/>;
 else if(kind==='kpi')content=<div className={styles.kpi}><span>{metricName(metric)} · selected rows</span><strong>{format(rowsTotal,metric)}</strong><small>{rows.length} displayed categories</small></div>;
 else if(kind==='gauge'){
  if(typeof target!=='number'||!Number.isSafeInteger(target)||target<=0)content=<p role="status">Gauge hidden: provide an explicit positive integer target to compare against selected rows.</p>;
  else {const ratio=rowsTotal/target,shown=Math.min(1,ratio),x=55+Math.min(310,310*shown);content=<svg className={styles.svg} viewBox="0 0 420 180" role="img" aria-label={`Selected ${metricName(metric)} ${format(rowsTotal,metric)} against explicit target ${format(target,metric)}${ratio>1?' (target exceeded)':''}`}><title>Selected value compared with the caller-supplied target</title><desc>The gauge scale ends at the explicit target; values above it are reported as exceeding the target.</desc><path d={arcPath(210,140,145,180,360)} fill="none" stroke="#e2e9eb" strokeWidth="24"/><path d={arcPath(210,140,145,180,180+180*shown)} fill="none" stroke="#276e68" strokeWidth="24"/><text x="210" y="105" textAnchor="middle" className={styles.gaugeValue}>{format(rowsTotal,metric)}</text><text x="210" y="130" textAnchor="middle">of target {format(target,metric)}{ratio>1?' · exceeded':''}</text></svg>;}
 }else if(kind==='pie'||kind==='donut'){
  const segments=pieSegments(rows);
  if(!segments.length)content=<p role="status">No positive selected values to draw; the exact table remains available.</p>;
  else content=<svg className={styles.svg} viewBox="0 0 300 270" role="img" aria-label={`${kind} chart for ${metricName(metric)}`}><title>{`${kind} of ${metricName(metric)} by category`}</title><desc>Category fractions use the sum of all selected values. See the exact value table for details.</desc>{segments.map((segment,index)=>segment.fullCircle?<circle key={segment.id} cx="150" cy="135" r={kind==='donut'?92:105} fill={colors[index%colors.length]}/>:<path key={segment.id} d={piePath(segment,105,kind==='donut'?54:0)} fill={colors[index%colors.length]} stroke="white" strokeWidth="1"><title>{segment.label}: {format(segment.value,metric)} ({(segment.fraction*100).toFixed(1)}%)</title></path>)}{kind==='donut'&&<circle cx="150" cy="135" r="49" fill="white"/>}</svg>;
 }else if(kind==='treemap'){
  if(rowsTotal===0)content=<p role="status">No positive selected values to size treemap cells.</p>;
  else {let x=0;content=<svg className={styles.svg} viewBox="0 0 760 300" role="img" aria-label={`Treemap of ${metricName(metric)} by category`}><title>Treemap sized by selected values</title><desc>Rectangle area is proportional to each category's selected value; exact values are listed below.</desc>{rows.map((row,index)=>{const width=760*row.value/rowsTotal,cell=<g key={row.id}><rect x={x} y="0" width={width} height="298" fill={colors[index%colors.length]} stroke="white" strokeWidth="2"><title>{row.label}: {format(row.value,metric)}</title></rect>{width>48&&<text x={x+8} y="28" fill="white">{short(row.label,Math.max(6,Math.floor(width/8)))}</text>}</g>;x+=width;return cell;})}</svg>;}
 }else if(kind==='funnel')content=<svg className={styles.svg} viewBox={`0 0 760 ${Math.max(210,rows.length*42+35)}`} role="img" aria-label={`Ranked categories by ${metricName(metric)}, not a conversion funnel`}><title>Ranked category counts, not conversion stages</title><desc>Each bar is an independent category. Widths are relative to the largest category; they do not imply stage-to-stage conversion.</desc>{rows.map((row,index)=>{const y=20+index*42,width=540*row.value/max;return <g key={row.id}><text x="5" y={y+16}>{short(row.label)}</text><rect x="180" y={y} width={Math.max(0,width)} height="23" rx="4" fill={colors[index%colors.length]}/><text x={190+width} y={y+16}>{format(row.value,metric)}</text></g>;})}</svg>;
 else if(kind==='waterfall'){
  if(rowsTotal===0)content=<p role="status">No positive contributions to show.</p>;
  else {let accumulated=0;const chartHeight=205,base=260;content=<svg className={styles.svg} viewBox={`0 0 ${Math.max(440,rows.length*58+80)} 300`} role="img" aria-label={`Cumulative positive contributions to ${metricName(metric)}`}><title>Cumulative category contributions</title><desc>Each category adds its positive selected value to a cumulative total. These are not signed changes over time.</desc>{rows.map((row,index)=>{const width=Math.max(6,Math.min(32,480/rows.length)),x=42+index*480/Math.max(1,rows.length);const prior=accumulated;accumulated+=row.value;const y=base-accumulated/rowsTotal*chartHeight,height=row.value/rowsTotal*chartHeight;return <g key={row.id}><rect x={x} y={y} width={width} height={height} fill={colors[index%colors.length]}><title>{row.label}: adds {format(row.value,metric)}; cumulative {format(accumulated,metric)}</title></rect>{prior>0&&<line x1={x-width/2} x2={x+width} y1={base-prior/rowsTotal*chartHeight} y2={base-prior/rowsTotal*chartHeight} stroke="#829298" strokeDasharray="3 3"/>}<text x={x+width/2} y="282" textAnchor="middle">{short(row.label,9)}</text></g>;})}</svg>;}
 }else if(kind==='combo'){
  const viewWidth=Math.max(440,rows.length*56+90),base=260,chartHeight=205,points=rows.map((row,index)=>({x:42+index*(viewWidth-84)/Math.max(1,rows.length-1),y:base-row.succeeded/Math.max(1,...rows.map(item=>item.attempts))*chartHeight}));
  content=<svg className={styles.svg} viewBox={`0 0 ${viewWidth} 300`} role="img" aria-label="Attempt columns and succeeded attempts line by date"><title>Attempt volume and successful attempts</title><desc>Columns show all attempts; the line shows successful attempts on the same numeric axis.</desc>{rows.map((row,index)=>{const x=42+index*(viewWidth-84)/Math.max(1,rows.length-1),width=Math.max(5,Math.min(32,(viewWidth-84)/Math.max(1,rows.length)*.6)),height=row.attempts/Math.max(1,...rows.map(item=>item.attempts))*chartHeight;return <g key={row.id}><rect x={x-width/2} y={base-height} width={width} height={height} fill={colors[index%colors.length]} opacity=".7"><title>{row.label}: {row.attempts} attempts</title></rect><text x={x} y="282" textAnchor="middle">{short(row.label,9)}</text></g>;})}<polyline points={points.map(point=>`${point.x},${point.y}`).join(' ')} fill="none" stroke="#a34645" strokeWidth="3"/>{points.map((point,index)=><circle key={rows[index].id} cx={point.x} cy={point.y} r="4" fill="#a34645"><title>{rows[index].label}: {rows[index].succeeded} succeeded</title></circle>)}</svg>;
 }else{
  const horizontal=kind==='bar',stacked=kind==='stacked-area';
  if(horizontal)content=<Segmented rows={rows} metric={metric} kind="bar"/>;
  else if(kind==='column'||kind==='stacked-column'||kind==='percent-column'||kind==='stacked-bar'||kind==='percent-bar')content=<Segmented rows={rows} metric={metric} kind={kind}/>;
  else {
   const maxValue=Math.max(1,...rows.map(row=>row.value)),width=Math.max(440,rows.length*56+80),base=260,high=55,points=rows.map((row,index)=>({x:40+index*(width-80)/Math.max(1,rows.length-1),value:stacked?row.succeeded:row.value,other:stacked?row.attempts-row.succeeded:0}));
   const y=(value:number)=>base-value/maxValue*(base-high),coords=points.map(point=>`${point.x},${y(point.value)}`).join(' ');
   if(kind==='area'||kind==='stacked-area'){
   const area=stacked?`${points.map(point=>`${point.x},${y(point.value)}`).join(' ')} ${points.slice().reverse().map(point=>`${point.x},${y(point.value+point.other)}`).join(' ')}`:`40,${base} ${coords} ${width-40},${base}`;
   const successArea=stacked?`40,${base} ${points.map(point=>`${point.x},${y(point.value)}`).join(' ')} ${width-40},${base}`:'';
    content=<svg className={styles.svg} viewBox={`0 0 ${width} 300`} role="img" aria-label={`${kind} chart of ${metricName(metric)}`}><title>{kind==='stacked-area'?'Succeeded and other attempts over time':`${metricName(metric)} over time`}</title><desc>{kind==='stacked-area'?'The lower filled area is successful attempts, with other attempts stacked above.':'Area height is proportional to the selected metric.'}</desc>{stacked&&<polygon points={area} fill="#edc98b" opacity=".7"/>}<polygon points={stacked?successArea:area} fill="#bdd4cf" opacity=".9"/>{stacked&&<polyline points={points.map(point=>`${point.x},${y(point.value)}`).join(' ')} fill="none" stroke="#276e68" strokeWidth="3"/>}{!stacked&&<polyline points={coords} fill="none" stroke="#276e68" strokeWidth="3"/>}{rows.map((row,index)=><g key={row.id}><circle cx={points[index].x} cy={y(points[index].value)} r="4" fill="#276e68"/><text x={points[index].x} y="282" textAnchor="middle">{short(row.label,9)}</text></g>)}</svg>;
   }else content=<svg className={styles.svg} viewBox={`0 0 ${width} 300`} role="img" aria-label={`${kind} chart of ${metricName(metric)}`}><title>{kind==='line'?'Line chart':`Chart: ${metricName(metric)}`}</title><desc>Points follow the input order. Day series are chronological.</desc><polyline points={coords} fill="none" stroke="#276e68" strokeWidth="3"/>{rows.map((row,index)=><g key={row.id}><circle cx={points[index].x} cy={y(points[index].value)} r="5" fill={colors[index%colors.length]}><title>{row.label}: {format(row.value,metric)}</title></circle><text x={points[index].x} y="282" textAnchor="middle">{short(row.label,9)}</text></g>)}</svg>;
  }
 }
 const title=`${kind.replaceAll('-',' ')} · ${metricName(metric)}`;
 const note=`${partial?(metric==='knownCostMicrousd'?'Partial known-cost evidence; unresolved charges are not represented as zero. ':'Partial source evidence; some rows may be omitted or invalid. '):''}${omitted>0?`${omitted} matching categories omitted from this view. `:''}${metric==='knownCostMicrousd'?'Cost values are recorded integer micro-USD.':'Values are observed attempt counts.'} Charts do not imply causality.`;
 return <figure className={frameClass} aria-labelledby={titleId} aria-describedby={compact?undefined:descriptionId}>
  <figcaption><h3 id={titleId} className={compact?styles.visuallyHidden:''}>{title}</h3><p id={descriptionId} className={compact?styles.visuallyHidden:''}>{note}</p></figcaption>
  <div className={styles.visual}>{content}</div>
  {!['table','matrix','kpi'].includes(kind)&&<Table rows={rows} metric={metric} totalValue={allTotal} selected={selected} onSelect={onSelect}/>}
  {kind==='kpi'&&rows.length>0&&<Table rows={rows} metric={metric} totalValue={allTotal} selected={selected} onSelect={onSelect}/>}
 </figure>;
}
