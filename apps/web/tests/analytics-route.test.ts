import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {POST} from '../app/api/analytics/route';
test('analytics API protects recorded data, rejects arbitrary paths and keeps unknown costs unresolved',async()=>{
 const oldToken=process.env.INTEGRATION_ACCESS_TOKEN,oldDb=process.env.APEX_CONTROL_DB_PATH;
 const dir=await mkdtemp(path.join(tmpdir(),'apex-analytics-route-'));
 process.env.INTEGRATION_ACCESS_TOKEN='analytics-test-token';process.env.APEX_CONTROL_DB_PATH=path.join(dir,'missing.sqlite');
 const req=(body:unknown,headers:Record<string,string>={})=>new Request('http://127.0.0.1:3010/api/analytics',{method:'POST',headers:{authorization:'Bearer analytics-test-token','content-type':'application/json',...headers},body:JSON.stringify(body)});
 try{
  assert.equal((await POST(req({source:'live'},{authorization:'Bearer wrong'}))).status,401);
  assert.equal((await POST(req({source:'live'},{origin:'https://untrusted.example',host:'127.0.0.1:3010'}))).status,401);
  assert.equal((await POST(req({source:'live',dbPath:'/etc/passwd'}))).status,400);
  assert.equal((await POST(req({source:'demo'}))).status,400);
  assert.equal((await POST(req({source:'live',days:400}))).status,400);
  assert.equal((await POST(req({source:'import',rows:'x'.repeat(2097153)}))).status,400);
  const empty=await POST(req({source:'live'}));assert.equal(empty.status,200);const snapshot=(await empty.json()).result;assert.equal(snapshot.kpis.attempts,0);assert.equal(snapshot.quality.selectionKnownCoverage,false);
  const now=Math.floor(Date.now()/1000),row={attemptId:'fixture-attempt',taskId:'fixture-task',tool:'fixture-tool',resource:'fixture-resource',startedAt:now-60,settledAt:now-1,outcome:'succeeded',actualCostMicrousd:null};
  const response=await POST(req({source:'import',days:7,rows:[row]}));assert.equal(response.status,200,await response.clone().text());const data=(await response.json()).result;
  assert.equal(data.kpis.succeeded,1);assert.equal(data.quality.unknownCostRows,1);assert.equal(data.kpis.costPerSuccessMicrousd,null);assert.equal(data.forecast.points.length,0);
  assert.equal(JSON.stringify(data).includes('analytics-test-token'),false);
 }finally{if(oldToken===undefined)delete process.env.INTEGRATION_ACCESS_TOKEN;else process.env.INTEGRATION_ACCESS_TOKEN=oldToken;if(oldDb===undefined)delete process.env.APEX_CONTROL_DB_PATH;else process.env.APEX_CONTROL_DB_PATH=oldDb;await rm(dir,{recursive:true,force:true});}
});
