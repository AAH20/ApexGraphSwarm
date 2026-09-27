export const VISUAL_KINDS=['bar','column','stacked-bar','stacked-column','percent-bar','percent-column','pie','donut','line','area','stacked-area','combo','treemap','waterfall','funnel','gauge','kpi','table','matrix','ribbon'] as const;
export type VisualKind=typeof VISUAL_KINDS[number];
export type AnalyticsMetric='attempts'|'succeeded'|'knownCostMicrousd';
export type AnalyticsDimension='tool'|'resource'|'day';
export type ChartDatum={id:string;label:string;value:number;attempts:number;succeeded:number};
export type AnalyticsReportSource={
 quality:{truncated?:boolean;invalidRows?:number;unknownCostRows?:number};
 cohorts:{tool:string;resource:string;attempts:number;succeeded:number;knownCostMicrousd:number;unknownCostRows:number}[];
 daily:{date:string;attempts:number;succeeded:number;knownCostMicrousd:number;unknownCostRows:number}[];
};
export type VisualData={rows:ChartDatum[];totalValue:number;omitted:number;partial:boolean};
export type PieSegment={id:string;label:string;value:number;startAngle:number;endAngle:number;fraction:number;fullCircle:boolean};
export function visualSupport(kind:VisualKind):{supported:boolean;reason?:string}{
 if(kind==='ribbon')return {supported:false,reason:'Ribbon charts require per-category values across multiple dates; the current event aggregates do not include that series.'};
 if(!VISUAL_KINDS.includes(kind))return {supported:false,reason:'Unknown chart type.'};
 return {supported:true};
}
type AggregateGroup={id:string;label:string;attempts:number;succeeded:number;knownCostMicrousd:number};

export class AnalyticsVisualDataError extends Error{
 constructor(message:string){super(message);this.name='AnalyticsVisualDataError';}
}

const MAX_GROUPS=20;
const METRICS:AnalyticsMetric[]=['attempts','succeeded','knownCostMicrousd'];
function requireCount(value:number,label:string):number{
 if(!Number.isSafeInteger(value)||value<0)throw new AnalyticsVisualDataError(`${label} must be a non-negative safe integer.`);
 return value;
}
function add(left:number,right:number,label:string):number{
 const sum=left+right;
 return requireCount(sum,label);
}
function valueFor(row:{attempts:number;succeeded:number;knownCostMicrousd:number},metric:AnalyticsMetric):number{
 if(!METRICS.includes(metric))throw new AnalyticsVisualDataError('Unsupported analytics metric.');
 return requireCount(row[metric],metric);
}
function safeDimension(label:string,dimension:AnalyticsDimension):{id:string;label:string}{
 if(typeof label!=='string')throw new AnalyticsVisualDataError(`Report ${dimension} label must be text.`);
 const normalized=label.trim()||`(unknown ${dimension})`;
 return {id:`${dimension}:${normalized}`,label:normalized};
}
export function buildVisualData(report:AnalyticsReportSource,dimension:AnalyticsDimension,metric:AnalyticsMetric,limit=12,query=''):VisualData{
 if(!report||!report.quality||!Array.isArray(report.cohorts)||!Array.isArray(report.daily))throw new AnalyticsVisualDataError('Analytics report shape is invalid.');
 if(!['tool','resource','day'].includes(dimension))throw new AnalyticsVisualDataError('Unsupported analytics dimension.');
 if(!METRICS.includes(metric))throw new AnalyticsVisualDataError('Unsupported analytics metric.');
 if(!Number.isInteger(limit)||limit<1||limit>MAX_GROUPS)throw new AnalyticsVisualDataError(`limit must be from 1 to ${MAX_GROUPS}.`);
 if(typeof query!=='string'||query.length>256)throw new AnalyticsVisualDataError('query must be at most 256 characters.');
 const needle=query.trim().toLocaleLowerCase('en-US');
 const groups=new Map<string,AggregateGroup>();
 let unknownCostRows=0;
 if(dimension==='day'){
  for(const item of report.daily){
   if(!item||typeof item.date!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(item.date))throw new AnalyticsVisualDataError('Daily report has an invalid UTC date.');
   const date=new Date(`${item.date}T00:00:00Z`);
   if(!Number.isFinite(date.getTime())||date.toISOString().slice(0,10)!==item.date)throw new AnalyticsVisualDataError('Daily report has an invalid UTC date.');
   const {id,label}=safeDimension(item.date,'day');
   if(groups.has(id))throw new AnalyticsVisualDataError('Daily report contains duplicate UTC dates.');
   const attempts=requireCount(item.attempts,'attempts'),succeeded=requireCount(item.succeeded,'succeeded');
   if(succeeded>attempts)throw new AnalyticsVisualDataError('Daily succeeded count exceeds attempts.');
   const knownCostMicrousd=requireCount(item.knownCostMicrousd,'knownCostMicrousd');
   unknownCostRows=add(unknownCostRows,requireCount(item.unknownCostRows,'unknownCostRows'),'unknownCostRows');
   groups.set(id,{id,label,attempts,succeeded,knownCostMicrousd});
  }
 }else{
  for(const item of report.cohorts){
   const name=dimension==='tool'?item.tool:item.resource;
   const {id,label}=safeDimension(name,dimension);
   const attempts=requireCount(item.attempts,'attempts'),succeeded=requireCount(item.succeeded,'succeeded');
   if(succeeded>attempts)throw new AnalyticsVisualDataError('Cohort succeeded count exceeds attempts.');
   const knownCostMicrousd=requireCount(item.knownCostMicrousd,'knownCostMicrousd');
   unknownCostRows=add(unknownCostRows,requireCount(item.unknownCostRows,'unknownCostRows'),'unknownCostRows');
   const previous=groups.get(id);
   groups.set(id,{id,label,attempts:add(previous?.attempts??0,attempts,'attempts'),
    succeeded:add(previous?.succeeded??0,succeeded,'succeeded'),
    knownCostMicrousd:add(previous?.knownCostMicrousd??0,knownCostMicrousd,'knownCostMicrousd')});
  }
 }
 let matching=[...groups.values()].filter(row=>!needle||row.label.toLocaleLowerCase('en-US').includes(needle))
  .map(row=>({...row,value:valueFor(row,metric)}));
 const selectionCount=matching.length;
 const chronological=dimension==='day';
 matching.sort((a,b)=>chronological?(a.label<b.label?-1:a.label>b.label?1:0):(b.value-a.value|| (a.label<b.label?-1:a.label>b.label?1:0)));
 if(chronological&&matching.length>limit)matching=matching.slice(matching.length-limit);
 const selected=matching.slice(0,limit);
 let totalValue=0;
 for(const row of selected)totalValue=add(totalValue,row.value,'displayed selection total');
 const rows=selected.map(({id,label,value,attempts,succeeded})=>({id,label,value,attempts,succeeded}));
 const invalidRows=report.quality.invalidRows??0,qualityUnknownCostRows=report.quality.unknownCostRows??0;
 if(typeof invalidRows!=='number'||!Number.isSafeInteger(invalidRows)||invalidRows<0)throw new AnalyticsVisualDataError('Report invalidRows must be a non-negative safe integer.');
 requireCount(qualityUnknownCostRows,'quality unknownCostRows');
 return {rows,totalValue,omitted:Math.max(0,selectionCount-rows.length),
  partial:report.quality.truncated===true||invalidRows>0||(metric==='knownCostMicrousd'&&(unknownCostRows>0||qualityUnknownCostRows>0))};
}

export function pieSegments(rows:readonly ChartDatum[]):PieSegment[]{
 if(!Array.isArray(rows)||rows.length>MAX_GROUPS)throw new AnalyticsVisualDataError(`Pie data must contain at most ${MAX_GROUPS} categories.`);
 const ids=new Set<string>();
 const values=rows.map(row=>{
  if(!row||typeof row.id!=='string'||!row.id||ids.has(row.id)||typeof row.label!=='string'||!row.label)throw new AnalyticsVisualDataError('Pie category identity is invalid.');
  ids.add(row.id);
  return requireCount(row.value,'pie value');
 });
 let total=0;for(const value of values)total=add(total,value,'pie total');
 if(total===0)return [];
 const positive=rows.map((row,index)=>({row,value:values[index]})).filter(item=>item.value>0);
 let cursor=-90;
 return positive.map(({row,value},index)=>{
  const fraction=value/total;
  const startAngle=cursor;
  const fullCircle=positive.length===1;
  const endAngle=fullCircle?startAngle+360:startAngle+fraction*360;
  cursor=endAngle;
  return {id:row.id,label:row.label,value,startAngle,endAngle,fraction,fullCircle};
 });
}
