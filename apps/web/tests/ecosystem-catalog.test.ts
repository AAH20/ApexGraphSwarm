import test from 'node:test';
import assert from 'node:assert/strict';
import {costLines,ecosystemCatalog,estimateEcosystemCost} from '../lib/ecosystem-catalog';
test('unknown ecosystem costs do not become a zero total',()=>{
 const result=estimateEcosystemCost([{id:'gateway',quantity:1000,usdPerUnit:.001}],10);
 assert.equal(result.knownSubtotalUsd,1); assert.equal(result.totalUsd,null);assert.equal(result.costPerSuccessUsd,null);assert.ok(result.missing.includes('active'));
});
test('complete explicit assumptions support cost per successful result',()=>{
 const result=estimateEcosystemCost(costLines.map(([id])=>({id,quantity:10,usdPerUnit:2})),7);
 assert.equal(result.totalUsd,costLines.length*20);assert.equal(result.costPerSuccessUsd,costLines.length*20/7);assert.equal(result.complete,true);
});
test('invalid, duplicate and overflow cost inputs fail closed',()=>{
 for(const value of [NaN,Infinity,-1]) assert.throws(()=>estimateEcosystemCost([{id:'model',quantity:value,usdPerUnit:1}],1));
 assert.throws(()=>estimateEcosystemCost([{id:'model',quantity:1,usdPerUnit:1},{id:'model',quantity:1,usdPerUnit:1}],1));
 assert.throws(()=>estimateEcosystemCost([{id:'model',quantity:1e300,usdPerUnit:1e300}],1));
 assert.throws(()=>estimateEcosystemCost([],1.5));
});
test('AX is an executor with a visible unverified scale boundary',()=>{
 const ax=ecosystemCatalog.find(item=>item.id==='google-ax')!;
 assert.equal(ax.layer,'executor');assert.match(ax.status,/planned/);assert.match(ax.limits,/No AX deployment or 150K-agent benchmark/);
});
