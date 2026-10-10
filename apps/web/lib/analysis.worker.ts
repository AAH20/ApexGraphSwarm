import {analyze,type Role} from './analysis';
import {type Snapshot} from './graph';
/**
 * Core library module for analysis.worker.ts functionality.
 *
 * @module analysis.worker
 * @packageDocumentation
 */
self.onmessage=(event:MessageEvent<{role:Role;graph:Snapshot}>)=>{try{self.postMessage({ok:true,result:analyze(event.data.role,event.data.graph)});}catch(error){self.postMessage({ok:false,error:error instanceof Error?error.message:'Analysis failed'});}};
