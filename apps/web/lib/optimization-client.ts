import {execFile} from 'node:child_process';
import path from 'node:path';
import {assertJsonPrecision} from './optimization-json';

// Only a fixed Python entry point is invoked; JSON never becomes shell syntax.
/**
 * Function optimizationOperation.
 *
 * @param {Record<string, unknown>} input - Description of input.
 * @returns {Promise<Record<string, unknown>>} Description of return value.
 *
 * @example
 * ```typescript
 * const result = optimizationOperation(...);
 * ```
 */
export async function optimizationOperation(input: Record<string, unknown>): Promise<Record<string, unknown>> {
 return new Promise((resolve,reject)=>{
  const child=execFile('python3',['-m','apexgraphswarm.lab'],{
   cwd:path.resolve(process.cwd(),'../..'), timeout:15000, maxBuffer:2*1024*1024, encoding:'utf8',
   env:{NODE_ENV:process.env.NODE_ENV||'production',PATH:process.env.PATH,LANG:'C.UTF-8',PYTHONIOENCODING:'utf-8',PYTHONDONTWRITEBYTECODE:'1',APEX_REPOSITORY_PATH:process.env.APEX_REPOSITORY_PATH,VLLM_METRICS_URL:process.env.VLLM_METRICS_URL,VLLM_METRICS_TOKEN:process.env.VLLM_METRICS_TOKEN},
  },(error,stdout)=>{
   try {
    const result=JSON.parse(stdout);
    if(error||result.error) reject(new Error(result.error||'Local experiment exceeded its execution limit.'));
    else {assertJsonPrecision(result);resolve(result);}
   } catch(error) { reject(error instanceof Error&&error.message.includes('precision')?error:new Error('The local experiment returned an invalid response.')); }
  });
  child.stdin?.on('error',()=>{});
  child.stdin?.end(JSON.stringify(input));
 });
}
