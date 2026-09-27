import test from 'node:test';
import assert from 'node:assert/strict';
import {GET, POST} from '../app/api/decisions/route';

test('decision API bounds requests, protects execution and exposes only safe configuration', async () => {
  const keys = ['INTEGRATION_ACCESS_TOKEN','LAYA_PREDICT_URL','LAYA_API_KEY','LAYA_COST_MICROUSD_PER_QUESTION','ANYJEV_PREDICT_URL','ANYJEV_API_KEY','ANYJEV_COST_MICROUSD_PER_QUESTION'];
  const saved = Object.fromEntries(keys.map(key => [key,process.env[key]]));
  for (const key of keys) delete process.env[key];
  process.env.INTEGRATION_ACCESS_TOKEN = 'decision-fixture-token';
  const body = {providers:['laya'],state:'Explicit fixture context.',questions:{route:{type:'choice',instructions:'Which queue?',criteria:{review:'Review evidence',defer:'Gather more evidence'}}},threshold:0.8,maxCostMicrousd:1000};
  const req = (value:unknown, headers:Record<string,string>={}) => new Request('http://127.0.0.1:3010/api/decisions',{method:'POST',headers:{'content-type':'application/json',authorization:'Bearer decision-fixture-token',...headers},body:JSON.stringify(value)});
  try {
    assert.equal((await POST(req(body,{authorization:'Bearer invalid'}))).status,401);
    assert.equal((await POST(req(body,{origin:'https://untrusted.example',host:'127.0.0.1:3010'}))).status,401);
    assert.equal((await POST(req(body,{'content-type':'text/plain'}))).status,415);
    assert.equal((await POST(req({...body,state:'x'.repeat(65537)}))).status,400);
    assert.equal((await POST(req({...body,url:'https://untrusted.example'}))).status,400);
    const response = await POST(req(body));
    assert.equal(response.status,200);
    const result = await response.json();
    assert.equal(result.results[0].status,'unconfigured');
    assert.equal(result.results[0].actualCostMicrousd,null);
    process.env.LAYA_PREDICT_URL='https://private.example/v1/systemone';
    process.env.LAYA_API_KEY='secret-fixture-key';
    const config = await GET().text();
    assert.equal(config.includes('private.example'),false);
    assert.equal(config.includes('secret-fixture-key'),false);
    assert.equal(config.includes('decision-fixture-token'),false);
  } finally {
    for (const key of keys) {if (saved[key]===undefined) delete process.env[key];else process.env[key]=saved[key];}
  }
});
