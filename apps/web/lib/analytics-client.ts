import {execFile} from 'node:child_process';
import path from 'node:path';
import {assertJsonPrecision} from './optimization-json';
export async function analyticsOperation(input:Record<string,unknown>){
 const root=path.resolve(process.cwd(),'../..');
 const dbPath=process.env.APEX_CONTROL_DB_PATH?path.resolve(process.env.APEX_CONTROL_DB_PATH):path.join(root,'.runtime','control.sqlite');
 return new Promise<Record<string,unknown>>((resolve,reject)=>{
  const child=execFile('python3',['-m','apexgraphswarm.analytics'],{cwd:root,timeout:15000,maxBuffer:4*1024*1024,encoding:'utf8',env:{NODE_ENV:process.env.NODE_ENV,PATH:process.env.PATH,LANG:'C.UTF-8',PYTHONDONTWRITEBYTECODE:'1'}},(error,stdout)=>{
   try{const result=JSON.parse(stdout);if(error||result.error)throw Error(result.error||'Analytics exceeded its processing limit.');assertJsonPrecision(result);resolve(result);}catch(error){reject(error instanceof Error?error:Error('Invalid analytics response.'));}
  });
  child.stdin?.on('error',()=>{});child.stdin?.end(JSON.stringify({...input,dbPath}));
 });
}
