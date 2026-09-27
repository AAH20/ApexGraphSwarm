import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {randomUUID} from 'node:crypto';
const token=readFileSync(new URL('../.env.local',import.meta.url),'utf8').split('\n').find(s=>s.startsWith('INTEGRATION_ACCESS_TOKEN='))?.slice('INTEGRATION_ACCESS_TOKEN='.length).trim();
assert.ok(token,'Configure the local workspace token first.');
const url='http://127.0.0.1:3010/api/control';
async function request(body,authorized=true,origin){const response=await fetch(url,{method:'POST',redirect:'error',headers:{'Content-Type':'application/json',...(authorized?{Authorization:`Bearer ${token}`}:{ }),...(origin?{Origin:origin}:{})},body:JSON.stringify(body)});return {status:response.status,body:await response.json()};}
assert.equal((await request({},false)).status,401);
assert.equal((await request({},true,'https://untrusted.example')).status,401);
assert.equal((await request({action:'status',runId:'invalid',dbPath:'/untrusted.sqlite'})).status,400);
const input={action:'createFixture',agents:30,idempotencyKey:randomUUID()};
const created=await request(input);assert.equal(created.status,200,created.body.error);const id=created.body.state.run.id;
const repeated=await request(input);assert.equal(repeated.body.state.run.id,id,'Idempotency must reuse the run.');
const advanced=await request({action:'advanceFixture',runId:id});assert.equal(advanced.status,200,advanced.body.error);assert.ok(['succeeded','completed'].includes(advanced.body.state.run.status));
const loaded=await request({action:'status',runId:id});assert.equal(loaded.status,200);assert.equal(loaded.body.state.tasks.length,30);assert.equal(loaded.body.state.run.spentMicrousd,0);assert.equal(loaded.body.state.run.reservedMicrousd,0);assert.ok(loaded.body.state.tasks.every(t=>t.result.modelCalls===0));
console.log(JSON.stringify({status:'passed',scope:'Authenticated Next API → Python → durable SQLite fixture',tasks:30,modelCalls:0,idempotency:'passed',persistence:'passed',authorization:'passed'}));
