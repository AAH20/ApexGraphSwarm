import assert from 'node:assert/strict';
import test from 'node:test';
import {adaptAnalyticsGraph,analyticsEdgeKey,filterAnalyticsGraph,MAX_ANALYTICS_GRAPH_EDGES,MAX_ANALYTICS_GRAPH_NODES} from '../lib/analytics-graph';
import {buildVisualData,pieSegments,visualSupport,VISUAL_KINDS,type AnalyticsReportSource,type ChartDatum,type VisualKind} from '../lib/analytics-visuals';

function report(overrides:Partial<AnalyticsReportSource>={}):AnalyticsReportSource{
 return {quality:{truncated:false,invalidRows:0,unknownCostRows:0},
  cohorts:[
   {tool:'tool-a',resource:'pool-a',attempts:3,succeeded:2,knownCostMicrousd:30,unknownCostRows:1},
   {tool:'tool-a',resource:'pool-b',attempts:4,succeeded:3,knownCostMicrousd:40,unknownCostRows:0},
   {tool:'tool-b',resource:'pool-a',attempts:5,succeeded:1,knownCostMicrousd:50,unknownCostRows:0},
  ],
  daily:[
   {date:'2026-09-03',attempts:2,succeeded:1,knownCostMicrousd:20,unknownCostRows:0},
   {date:'2026-09-01',attempts:1,succeeded:1,knownCostMicrousd:10,unknownCostRows:0},
   {date:'2026-09-02',attempts:3,succeeded:2,knownCostMicrousd:30,unknownCostRows:1},
  ],...overrides};
}

function graphFixture(overrides:Record<string,unknown>={}){
 return {nodes:[{id:'tool:review',label:'review',kind:'tool',privatePayload:'DO_NOT_COPY'},
  {id:'resource:model',label:'model pool',kind:'resource'}],
  edges:[{source:'tool:review',target:'resource:model',attempts:3,knownCostMicrousd:30,receipt:'DO_NOT_COPY'}],...overrides} as any;
}

test('visual aggregates use the displayed-category denominator and report omitted categories',()=>{
 const result=buildVisualData(report(), 'tool','attempts',1);
 assert.equal(result.totalValue,7);
 assert.equal(result.rows.length,1);
 assert.equal(result.rows[0].label,'tool-a');
 assert.equal(result.omitted,1);
 assert.deepEqual(result.rows[0],{id:'tool:tool-a',label:'tool-a',value:7,attempts:7,succeeded:5});
});

test('known-cost charts keep unknown liabilities out of totals and retain partial status',()=>{
 const result=buildVisualData(report(), 'tool','knownCostMicrousd',1);
 assert.equal(result.totalValue,70);
 assert.equal(result.rows[0].value,70);
 assert.equal(result.omitted,1);
 assert.equal(result.partial,true);
 const attempts=buildVisualData(report(), 'tool','attempts',10);
 assert.equal(attempts.partial,false);
});

test('daily visual data sorts chronologically and validates duplicate-free UTC categories',()=>{
 const result=buildVisualData(report(), 'day','attempts',10);
 assert.deepEqual(result.rows.map(row=>row.label),['2026-09-01','2026-09-02','2026-09-03']);
 assert.equal(result.totalValue,6);
 assert.equal(result.partial,false);
 assert.throws(()=>buildVisualData(report({daily:[{date:'2026-02-30',attempts:1,succeeded:1,knownCostMicrousd:1,unknownCostRows:0}]}),'day','attempts'),/UTC date/);
});

test('visual bounds, invalid aggregates, and partial source snapshots fail closed or stay flagged',()=>{
 assert.throws(()=>buildVisualData(report(),'tool','attempts',21),/limit/);
 assert.throws(()=>buildVisualData(report(),'tool','attempts',12,'x'.repeat(257)),/query/);
 assert.throws(()=>buildVisualData(report({quality:{truncated:false,invalidRows:-1,unknownCostRows:0}}),'tool','attempts'),/invalidRows/);
 const truncated=buildVisualData(report({quality:{truncated:true,invalidRows:0,unknownCostRows:0}}),'resource','attempts');
 assert.equal(truncated.partial,true);
});

test('chart support is explicit and does not invent a ribbon series from aggregate data',()=>{
 assert.ok(VISUAL_KINDS.includes('bar'));
 assert.equal(visualSupport('bar').supported,true);
 const ribbon=visualSupport('ribbon');
 assert.equal(ribbon.supported,false);
 assert.match(ribbon.reason||'',/per-category values across multiple dates/);
 assert.equal(visualSupport('unsupported' as VisualKind).supported,false);
});

test('pie geometry handles empty, zero, and singleton categories without NaN',()=>{
 assert.deepEqual(pieSegments([]),[]);
 const zero:ChartDatum={id:'zero',label:'zero',value:0,attempts:0,succeeded:0};
 assert.deepEqual(pieSegments([zero]),[]);
 const only:ChartDatum={id:'only',label:'only',value:7,attempts:7,succeeded:7};
 const one=pieSegments([only]);
 assert.equal(one.length,1);
 assert.equal(one[0].fullCircle,true);
 assert.equal(one[0].fraction,1);
 assert.equal(one[0].endAngle-one[0].startAngle,360);
 const many=pieSegments([only,{id:'second',label:'second',value:3,attempts:3,succeeded:2}]);
 assert.ok(many.every(segment=>Number.isFinite(segment.startAngle)&&Number.isFinite(segment.endAngle)));
 assert.ok(Math.abs(many.reduce((sum,segment)=>sum+segment.fraction,0)-1)<1e-12);
});

test('analytics graph carries provenance, redacts payload extras, and marks edge known-cost completeness',()=>{
 const full=adaptAnalyticsGraph(graphFixture(),'live',{unknownCostRows:0,invalidRows:0,truncated:false,selectionKnownCoverage:true});
 assert.equal(full.quality.evidence,'aggregated');
 assert.equal(full.edges[0].relation,'observed tool-to-resource usage');
 assert.equal(full.nodes.find(node=>node.id==='tool:review')?.kind,'function');
 assert.equal(full.nodes.find(node=>node.id==='resource:model')?.kind,'external');
 const metric=full.edgeMetrics.get(analyticsEdgeKey('tool:review','resource:model'));
 assert.deepEqual(metric,{attempts:3,knownCostMicrousd:30,complete:true});
 assert.ok(!JSON.stringify(full).includes('DO_NOT_COPY'));
 const partial=adaptAnalyticsGraph(graphFixture(),'live',{unknownCostRows:1,invalidRows:0,truncated:false,selectionKnownCoverage:true});
 assert.equal(partial.edgeMetrics.get(analyticsEdgeKey('tool:review','resource:model'))?.complete,false);
 assert.equal(adaptAnalyticsGraph(graphFixture(),'demo').quality.evidence,'illustrative');
});

test('analytics graph rejects bad identities and keeps only bounded endpoint-valid edges',()=>{
 const input=graphFixture({nodes:[
  {id:'tool:a',label:'A',kind:'tool'}, {id:'resource:b',label:'B',kind:'resource'},
  {id:'tool:a',label:'duplicate',kind:'tool'}, {id:'bad\nnode',label:'bad',kind:'tool'},
  {id:'tool:c',label:'wrong kind',kind:'function'},
 ],edges:[
  {source:'tool:a',target:'resource:b',attempts:2,knownCostMicrousd:9},
  {source:'tool:a',target:'missing',attempts:1,knownCostMicrousd:1},
  {source:'tool:a',target:'resource:b',attempts:0,knownCostMicrousd:1},
  {source:'tool:a',target:'resource:b',attempts:1,knownCostMicrousd:Number.MAX_SAFE_INTEGER},
 ]});
 const result=adaptAnalyticsGraph(input,'import',{unknownCostRows:0,invalidRows:0,truncated:false,selectionKnownCoverage:true});
 const ids=new Set(result.nodes.map(node=>node.id));
 assert.equal(result.quality.invalidNodes,3);
 assert.equal(result.quality.invalidEdges,3);
 assert.ok(result.edges.every(edge=>ids.has(edge.source)&&ids.has(edge.target)));
 assert.ok(!JSON.stringify(result).includes('wrong kind'));
});

test('analytics graph caps nodes and edges while preserving explicit omission counts',()=>{
 const nodes=[...Array.from({length:25},(_,i)=>({id:`tool:${i}`,label:`tool ${i}`,kind:'tool'})),
  ...Array.from({length:25},(_,i)=>({id:`resource:${i}`,label:`resource ${i}`,kind:'resource'}))];
 const edges=[];
 for(let tool=0;tool<25;tool++)for(let resource=0;resource<25;resource++)edges.push({source:`tool:${tool}`,target:`resource:${resource}`,attempts:1,knownCostMicrousd:1});
 const result=adaptAnalyticsGraph({nodes,edges} as any,'live',{unknownCostRows:0,invalidRows:0,truncated:false,selectionKnownCoverage:true});
 assert.equal(result.nodes.length,50);
 assert.equal(result.edges.length,MAX_ANALYTICS_GRAPH_EDGES);
 assert.equal(result.quality.omittedNodes,0);
 assert.equal(result.quality.omittedEdges,25);
 assert.ok(result.edges.every(edge=>result.nodes.some(node=>node.id===edge.source)&&result.nodes.some(node=>node.id===edge.target)));
 assert.equal(MAX_ANALYTICS_GRAPH_NODES,200);
});

test('graph filters preserve induced endpoints and restrict a selection to its one-hop neighborhood',()=>{
 const graph=adaptAnalyticsGraph({nodes:[
  {id:'tool:a',label:'alpha',kind:'tool'}, {id:'resource:x',label:'x',kind:'resource'},
  {id:'resource:y',label:'y',kind:'resource'}, {id:'tool:b',label:'beta',kind:'tool'}],
  edges:[{source:'tool:a',target:'resource:x',attempts:2,knownCostMicrousd:3},
   {source:'tool:a',target:'resource:y',attempts:1,knownCostMicrousd:1},
   {source:'tool:b',target:'resource:y',attempts:9,knownCostMicrousd:4}]},'live',
  {unknownCostRows:0,invalidRows:0,truncated:false,selectionKnownCoverage:true});
 const toolOnly=filterAnalyticsGraph(graph,{category:'tool'});
 assert.equal(toolOnly.nodes.length,2);
 assert.equal(toolOnly.edges.length,0);
 const neighborhood=filterAnalyticsGraph(graph,{selected:'tool:a',neighborhoodOnly:true});
 assert.deepEqual(new Set(neighborhood.nodes.map(node=>node.id)),new Set(['tool:a','resource:x','resource:y']));
 assert.ok(neighborhood.edges.every(edge=>neighborhood.nodes.some(node=>node.id===edge.source)&&neighborhood.nodes.some(node=>node.id===edge.target)));
 const query=filterAnalyticsGraph(graph,{query:'RESOURCE:X'});
 assert.deepEqual(query.nodes.map(node=>node.id),['resource:x']);
 assert.equal(query.edges.length,0);
});
