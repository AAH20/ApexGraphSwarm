import type {DecisionAnswer, DecisionProvider, DecisionQuestion, DecisionResult} from './decision-types';

/**
 * Core library module for decision fixture.ts functionality.
 *
 * @module decision-fixture
 * @packageDocumentation
 */
/**
 * Function fixtureAnswer.
 *
 * @param {string} id - Description of id.
 * @param {DecisionQuestion['type']} type - Description of type.
 * @param {string|number} value - Description of value.
 * @param {Record<string,number>} distribution - Description of distribution.
 * @param {number} confidence - Description of confidence.
 * @param {number} threshold - Description of threshold.
 * @returns {DecisionAnswer} Description of return value.
 *
 * @example
 * ```typescript
 * const result = fixtureAnswer(..., ..., ..., ..., ..., ...);
 * ```
 */
function fixtureAnswer(id:string,type:DecisionQuestion['type'],value:string|number,distribution:Record<string,number>,confidence:number,threshold:number):DecisionAnswer {
 return {id,type,value,distribution,confidence,reviewRequired:confidence<threshold};
}

/**
 * Function peakedDistribution.
 *
 * @param {string[]} labels - Description of labels.
 * @param {number} winnerIndex - Description of winnerIndex.
 * @param {number} peak - Description of peak.
 * @returns {Record<string,number>} Description of return value.
 *
 * @example
 * ```typescript
 * const result = peakedDistribution(..., ..., ...);
 * ```
 */
function peakedDistribution(labels:string[],winnerIndex:number,peak:number):Record<string,number> {
 if(!labels.length)return {};
 if(labels.length===1)return {[labels[0]]:1};
 const remainder=(1-peak)/(labels.length-1);
 return Object.fromEntries(labels.map((label,index)=>[label,index===winnerIndex?peak:remainder]));
}

/** Synthetic, deterministic examples for visualizing the response schema; never calls a provider. */
export function buildDecisionFixture(provider:DecisionProvider,questions:Record<string,DecisionQuestion>,threshold=0.75):DecisionResult {
 const yesProbability=provider==='laya'?0.68:0.41;
 const confidence=provider==='laya'?0.68:0.59;
 const answers=Object.entries(questions).map(([id,question])=>{
  if(question.type==='noul'){
   return fixtureAnswer(id,'noul',yesProbability,{false:1-yesProbability,true:yesProbability},Math.max(yesProbability,1-yesProbability),threshold);
  }
  if(question.type==='choice'){
   const options=Array.isArray(question.criteria)?question.criteria:['Option A','Option B'];
   const winnerIndex=provider==='laya'?0:Math.min(1,options.length-1);
   const distribution=peakedDistribution(options,winnerIndex,confidence);
   const winningProbability=Math.max(...Object.values(distribution));
   return fixtureAnswer(id,'choice',options[winnerIndex],distribution,winningProbability,threshold);
  }
  const criteria=Array.isArray(question.criteria)?question.criteria:question.criteria?Object.keys(question.criteria):['0 = low','1 = moderate','2 = high'];
  const levels=Math.max(1,Math.min(12,criteria.length));
  const winnerIndex=Math.min(levels-1,provider==='laya'?3:2);
  const labels=Array.from({length:levels},(_,index)=>String(index));
  const distribution=peakedDistribution(labels,winnerIndex,confidence);
  return fixtureAnswer(id,'score',winnerIndex,distribution,Math.max(...Object.values(distribution)),threshold);
 });
 return {
  provider,status:'succeeded',model:`Fixture: ${provider==='laya'?'Laya':'AnyJev'} example`,elapsedMs:0,
  estimatedCostMicrousd:null,actualCostMicrousd:null,answers,
  warnings:['Synthetic fixture only. No provider was called.'],
 };
}
