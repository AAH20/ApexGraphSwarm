import assert from 'node:assert/strict';
import test from 'node:test';
import {AnalyticsVisualDataError,VISUAL_KINDS,buildVisualData,pieSegments,visualSupport,type AnalyticsReportSource,type ChartDatum} from '../lib/analytics-visuals';

const report:AnalyticsReportSource={
 quality:{truncated:false,invalidRows:0,unknownCostRows:2},
 cohorts:[
  {tool:'review',resource:'model-a',attempts:4,succeeded:3,knownCostMicrousd:500,unknownCostRows:1},
  {tool:'review',resource:'model-b',attempts:2,succeeded:1,knownCostMicrousd:200,unknownCostRows:0},
  {tool:'compile',resource:'local',attempts:3,succeeded:3,knownCostMicrousd:0,unknownCostRows:1},
 ],
 daily:[
  {date:'2026-09-23',attempts:1,succeeded:1,knownCostMicrousd:10,unknownCostRows:0},
  {date:'2026-09-24',attempts:2,succeeded:1,knownCostMicrousd:20,unknownCostRows:1},
  {date:'2026-09-25',attempts:3,succeeded:2,knownCostMicrousd:30,unknownCostRows:0},
  {date:'2026-09-26',attempts:4,succeeded:2,knownCostMicrousd:40,unknownCostRows:0},
 ],
};
const datum=(id:string,value:number):ChartDatum=>({id,label:id,value,attempts:value,succeeded:value});

test('tool and resource dimensions aggregate separate cohorts without inventing an Others bucket',()=>{
 const tools=buildVisualData(report,'tool','attempts');
 assert.deepEqual(tools.rows.map(row=>[row.label,row.value,row.attempts,row.succeeded]),[['review',6,6,4],['compile',3,3,3]]);
 assert.equal(tools.totalValue,9);
 const resources=buildVisualData(report,'resource','knownCostMicrousd');
 assert.equal(resources.rows.length,3);
 assert.equal(resources.totalValue,700);
 assert.equal(resources.omitted,0);
 assert.equal(resources.partial,true);
 assert.equal(resources.rows.some(row=>row.label==='Other'),false);
});

test('limit and query report display totals and omitted matching categories explicitly',()=>{
 const selected=buildVisualData(report,'resource','attempts',1,'model');
 assert.equal(selected.rows.length,1);
 assert.equal(selected.rows[0].label,'model-a');
 assert.equal(selected.totalValue,4);
 assert.equal(selected.omitted,1);
 assert.equal(selected.partial,false);
});

test('daily series retain latest N dates in chronological order',()=>{
 const latest=buildVisualData(report,'day','attempts',2);
 assert.deepEqual(latest.rows.map(row=>row.label),['2026-09-25','2026-09-26']);
 assert.equal(latest.totalValue,7);
 assert.equal(latest.omitted,2);
 assert.throws(()=>buildVisualData({...report,daily:[report.daily[0],report.daily[0]]},'day','attempts'),/duplicate UTC dates/);
});

test('unknown costs mark cost charts partial but do not taint complete count charts',()=>{
 assert.equal(buildVisualData(report,'tool','knownCostMicrousd').partial,true);
 assert.equal(buildVisualData(report,'tool','attempts').partial,false);
 assert.equal(buildVisualData({...report,quality:{...report.quality,truncated:true}},'tool','succeeded').partial,true);
});

test('pie geometry handles zero and one positive category without NaN or fake slices',()=>{
 assert.deepEqual(pieSegments([]),[]);
 assert.deepEqual(pieSegments([datum('zero-a',0),datum('zero-b',0)]),[]);
 const single=pieSegments([datum('zero',0),datum('one',5)]);
 assert.equal(single.length,1);
 assert.deepEqual(single[0],{id:'one',label:'one',value:5,startAngle:-90,endAngle:270,fraction:1,fullCircle:true});
 const split=pieSegments([datum('a',1),datum('b',3)]);
 assert.equal(split.length,2);
 assert.ok(split.every(part=>Number.isFinite(part.startAngle)&&Number.isFinite(part.endAngle)&&Number.isFinite(part.fraction)));
 assert.ok(Math.abs(split.reduce((sum,part)=>sum+part.fraction,0)-1)<1e-12);
});

test('visual support catalog is exact and ribbon states its missing series requirement',()=>{
 assert.equal(VISUAL_KINDS.length,20);
 assert.equal(new Set(VISUAL_KINDS).size,20);
 assert.deepEqual(visualSupport('ribbon'),{supported:false,reason:'Ribbon charts require per-category values across multiple dates; the current event aggregates do not include that series.'});
 assert.deepEqual(visualSupport('treemap'),{supported:true});
});

test('aggregate inputs reject negative, inconsistent, overflowing, and invalid date records',()=>{
 assert.throws(()=>buildVisualData({...report,cohorts:[{...report.cohorts[0],knownCostMicrousd:-1}]},'tool','knownCostMicrousd'),AnalyticsVisualDataError);
 assert.throws(()=>buildVisualData({...report,cohorts:[{...report.cohorts[0],succeeded:5}]},'tool','attempts'),/exceeds attempts/);
 assert.throws(()=>buildVisualData({...report,cohorts:[{...report.cohorts[0],attempts:Number.MAX_SAFE_INTEGER},{...report.cohorts[0],attempts:1}]},'tool','attempts'),AnalyticsVisualDataError);
 assert.throws(()=>buildVisualData({...report,daily:[{...report.daily[0],date:'2026-02-31'}]},'day','attempts'),/invalid UTC date/);
});

test('pie geometry rejects negative or unsafe values rather than drawing misleading slices',()=>{
 assert.throws(()=>pieSegments([datum('negative',-1)]),AnalyticsVisualDataError);
 assert.throws(()=>pieSegments([datum('overflow',Number.MAX_SAFE_INTEGER),datum('extra',1)]),AnalyticsVisualDataError);
});
