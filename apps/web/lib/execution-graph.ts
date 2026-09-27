export type ExecutionNode={id:string;kind:string;label:string;status?:string;reservedMicrousd?:number|null;actualMicrousd?:number|null;details?:Record<string,unknown>;explanations?:string[]};
export type ExecutionEdge={id:string;source:string;target:string;kind:string;label?:string};
export type ExecutionGraph={version:1;runId:string;nodes:ExecutionNode[];edges:ExecutionEdge[];summary:{nodeCount:number;edgeCount:number;omittedNodes:number;omittedEdges:number;attemptCoverage:{expected:number;recorded:number;missing:number;complete:boolean;returned?:number};allCostsResolved:boolean;knownActualMicrousd:number;unknownCostAttempts:number};limitations:string[];truncated:boolean};
export const EXECUTION_KINDS=['run','agent','task','attempt','principal','worker','grant','resource','specialist_contract'] as const;
export function executionView(graph:ExecutionGraph,query:string,kind:string,focusId:string|null,neighborhood:boolean,limit=120){
 const search=query.trim().toLowerCase(),connected=new Set<string>();
 if(focusId){connected.add(focusId);for(const edge of graph.edges){if(edge.source===focusId)connected.add(edge.target);if(edge.target===focusId)connected.add(edge.source);}}
 const matches=graph.nodes.filter(node=>(kind==='all'||kind===node.kind)&&(!search||`${node.label} ${node.id} ${node.status||''}`.toLowerCase().includes(search))&&(!neighborhood||!focusId||connected.has(node.id)));
 const selected=matches.find(node=>node.id===focusId);
 const ordered=selected?[selected,...matches.filter(node=>node.id!==focusId)]:matches;
 const nodes=ordered.slice(0,limit),ids=new Set(nodes.map(node=>node.id));
 return {nodes,edges:graph.edges.filter(edge=>ids.has(edge.source)&&ids.has(edge.target)),matched:matches.length,omitted:matches.length-nodes.length};
}
export function executionLayout(nodes:ExecutionNode[]){
 const kinds=EXECUTION_KINDS.filter(kind=>nodes.some(node=>node.kind===kind));
 const positions=new Map<string,{x:number;y:number}>();let rows=1;
 kinds.forEach((kind,column)=>{let row=0;for(const node of nodes)if(node.kind===kind){positions.set(node.id,{x:30+column*245,y:50+row*82});row++;}rows=Math.max(rows,row);});
 return {positions,width:Math.max(700,kinds.length*245+30),height:Math.max(260,rows*82+70),kinds};
}
