import {formatMicrousd} from '../lib/format-microusd';
import assert from 'node:assert/strict';
import test from 'node:test';
import {POST} from '../app/api/optimization/route';
import {assertJsonPrecision} from '../lib/optimization-json';
import {optimizationExamples} from '../lib/optimization-examples';

test('browser cost JSON rejects silently rounded integers',()=>{assert.throws(()=>assertJsonPrecision({cost:9007199254740992}),/precision/);assert.doesNotThrow(()=>assertJsonPrecision({cost:9007199254740991,duration:0.5}));});

test('optimization boundary requires auth, origin and bounded valid JSON; examples execute locally',async()=>{
 const previous=process.env.INTEGRATION_ACCESS_TOKEN;const metrics=process.env.VLLM_METRICS_URL;delete process.env.VLLM_METRICS_URL;
 process.env.INTEGRATION_ACCESS_TOKEN='optimization-test-token';
 const request=(body:unknown,headers:Record<string,string>={})=>new Request('http://127.0.0.1:3010/api/optimization',{method:'POST',headers:{authorization:'Bearer optimization-test-token','content-type':'application/json',...headers},body:JSON.stringify(body)});
 try{
  assert.equal((await POST(request({action:'benchmark'},{authorization:'Bearer wrong'}))).status,401);
  assert.equal((await POST(request({action:'benchmark'},{origin:'https://untrusted.example',host:'127.0.0.1:3010'}))).status,401);
  assert.equal((await POST(request({action:'benchmark'},{'content-type':'text/plain'}))).status,415);
  assert.equal((await POST(request({action:'schedule',budget_microusd:9007199254740992}))).status,400);
  assert.equal((await POST(request({action:'shell',command:'echo unsafe'}))).status,400);
  assert.equal((await POST(request({action:'waves',data:'x'.repeat(131073)}))).status,400);
  for(const example of optimizationExamples){
   const response=await POST(request(example.payload));
   assert.equal(response.status,200,`${example.title}: ${await response.clone().text()}`);
   const data=await response.json();assert.equal(typeof data.result,'object');assert.ok(!data.result.error);
  }
 }finally{if(metrics!==undefined)process.env.VLLM_METRICS_URL=metrics;if(previous===undefined)delete process.env.INTEGRATION_ACCESS_TOKEN;else process.env.INTEGRATION_ACCESS_TOKEN=previous;}
});

test('microUSD currency preserves exact integer digits and labels unknowns',()=>{assert.equal(formatMicrousd(9007199254740991),'$9007199254.740991');assert.equal(formatMicrousd(1),'$0.000001');assert.equal(formatMicrousd(null),'Unknown');assert.ok(formatMicrousd(1.5).startsWith('≈'));});
