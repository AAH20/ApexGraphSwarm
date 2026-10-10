import {assertJsonPrecision} from './optimization-json';
import {execFile} from 'node:child_process';
import path from 'node:path';
import {mkdir} from 'node:fs/promises';
/**
 * Function controlOperation.
 *
 * @param {Record<string,unknown>} input - Description of input.
 *
 * @example
 * ```typescript
 * const result = controlOperation(...);
 * ```
 */
export async function controlOperation(input:Record<string,unknown>){
 const root=path.resolve(process.cwd(),'../..'),runtime=path.join(root,'.runtime'),dbPath=process.env.APEX_CONTROL_DB_PATH?path.resolve(process.env.APEX_CONTROL_DB_PATH):path.join(runtime,'control.sqlite');
 if(input.action!=='executionGraph')await mkdir(path.dirname(dbPath),{recursive:true,mode:0o700});
 return new Promise<unknown>((resolve,reject)=>{
  const child=execFile('python3',['-m',input.action==='executionGraph'?'apexgraphswarm.execution_graph':'apexgraphswarm.preview'],{cwd:root,timeout:20000,maxBuffer:2*1024*1024,encoding:'utf8',env:{NODE_ENV:process.env.NODE_ENV,PATH:process.env.PATH,LANG:'C.UTF-8',PYTHONDONTWRITEBYTECODE:'1'}},(error,stdout)=>{
   let result:unknown;try{result=JSON.parse(stdout);}catch{reject(new Error('Local control plane returned invalid JSON.'));return;}
   try{assertJsonPrecision(result);}catch{reject(new Error('Control data exceeds safe browser numeric precision. Inspect exact integers with the Python CLI.'));return;}
   const body=result as {error?:string};if(error||body.error)reject(new Error(body.error||'Control operation failed.'));else resolve(result);
  });
  child.stdin?.end(JSON.stringify(input.action==='executionGraph'?{runId:input.runId,dbPath}:{...input,dbPath}));
 });
}
