import {execFile} from 'node:child_process';
import path from 'node:path';
import {mkdir} from 'node:fs/promises';
export async function controlOperation(input:Record<string,unknown>){
 const root=path.resolve(process.cwd(),'../..'),runtime=path.join(root,'.runtime');
 await mkdir(runtime,{recursive:true,mode:0o700});
 return new Promise<unknown>((resolve,reject)=>{
  const child=execFile('python3',['-m','apexgraphswarm.preview'],{cwd:root,timeout:20000,maxBuffer:2*1024*1024,encoding:'utf8'},(error,stdout)=>{
   try{const result=JSON.parse(stdout);if(error||result.error)reject(new Error(result.error||'Control operation failed.'));else resolve(result);}catch{reject(new Error('Local control plane returned an invalid response.'));}
  });
  child.stdin?.end(JSON.stringify({...input,dbPath:path.join(runtime,'control.sqlite')}));
 });
}
