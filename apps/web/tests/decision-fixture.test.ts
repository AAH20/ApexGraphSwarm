import test from 'node:test';
import assert from 'node:assert/strict';
import {buildDecisionFixture} from '../lib/decision-fixture';
import type {DecisionQuestion} from '../lib/decision-types';

function close(actual:number,expected:number,message:string){assert.ok(Math.abs(actual-expected)<1e-10,`${message}: ${actual} != ${expected}`);}

test('choice fixture distributions are normalized and agree with selected answer confidence',()=>{
 for(const count of [2,3,12])for(const provider of ['laya','anyjev'] as const){
  const options=Array.from({length:count},(_,index)=>`Option ${index+1}`);
  const result=buildDecisionFixture(provider,{pick:{type:'choice',instructions:'Select an option.',criteria:options}});
  const answer=result.answers[0];
  const total=Object.values(answer.distribution).reduce((sum,value)=>sum+value,0);
  close(total,1,`${count}-option probability total`);
  close(Math.max(...Object.values(answer.distribution)),answer.confidence,'winner probability/confidence');
  assert.equal(answer.value,provider==='laya'?options[0]:options[1]);
  assert.equal(result.estimatedCostMicrousd,null);
  assert.equal(result.actualCostMicrousd,null);
  assert.equal(result.elapsedMs,0);
 }
});

test('Noul fixture represents P(Yes) and maps its Boolean distribution to the likely outcome',()=>{
 const question={binary:{type:'noul',instructions:'Is the evidence sufficient? Answer yes or no.'}} satisfies Record<string,DecisionQuestion>;
 const laya=buildDecisionFixture('laya',question).answers[0];
 assert.equal(laya.value,0.68);
 close(laya.distribution.true,0.68,'P(Yes)');
 close(laya.distribution.false,0.32,'P(No)');
 close(Math.max(...Object.values(laya.distribution)),laya.confidence,'Laya winning probability');
 const anyjev=buildDecisionFixture('anyjev',question).answers[0];
 assert.equal(anyjev.value,0.41);
 close(anyjev.distribution.true,0.41,'AnyJev P(Yes)');
 close(anyjev.distribution.false,0.59,'AnyJev P(No)');
 close(Math.max(...Object.values(anyjev.distribution)),anyjev.confidence,'AnyJev winning probability');
});

test('score fixtures remain criterion indices and probabilities normalize for several scale sizes',()=>{
 for(const count of [2,3,5,12]){
  const criteria=Array.from({length:count},(_,index)=>`${index} = band ${index}`);
  const result=buildDecisionFixture('laya',{score:{type:'score',instructions:'Score from zero.',criteria}});
  const answer=result.answers[0];
  assert.equal(answer.value,Math.min(3,count-1));
  close(Object.values(answer.distribution).reduce((sum,value)=>sum+value,0),1,'score distribution total');
  close(Math.max(...Object.values(answer.distribution)),answer.confidence,'score winning probability/confidence');
  assert.ok(Number(answer.value)>=0&&Number(answer.value)<count);
 }
});

test('reviewRequired follows supplied fixture threshold and fixture remains explicitly synthetic',()=>{
 const question={ready:{type:'noul',instructions:'Is it ready? Answer yes or no.'}} satisfies Record<string,DecisionQuestion>;
 const result=buildDecisionFixture('anyjev',question,0.6);
 assert.equal(result.answers[0].reviewRequired,true);
 assert.match(result.model??'',/Fixture/);
 assert.match(result.warnings[0],/No provider was called/);
});
