import assert from 'node:assert/strict';
import test from 'node:test';
import {stackedAttemptShares,visualTooltipDetails} from '../lib/chart-tooltip-details';
import type {ChartDatum} from '../lib/analytics-visuals';

const detailsByLabel=(details:{label:string;value:string}[])=>Object.fromEntries(details.map(item=>[item.label,item.value]));

test('tooltip shares expose displayed and filtered denominators with one-decimal precision',()=>{
 const row:ChartDatum={id:'a',label:'alpha',value:1,attempts:7,succeeded:2};
 const details=detailsByLabel(visualTooltipDetails(row,'attempts',6,12));
 assert.equal(details['Share of displayed rows'],'16.7% (1 / 6)');
 assert.equal(details['Share of query matches'],'8.3% (1 / 12)');
 assert.equal(details['Success / attempts'],'28.6% (2 / 7)');
 assert.equal(details['Other attempts'],'5');
});

test('stacked attempt segments form a complete partition without changing the category denominator',()=>{
 const shares=stackedAttemptShares(7,2);
 assert.equal(shares.succeeded,2/7);
 assert.equal(shares.other,5/7);
 assert.ok(Math.abs(shares.succeeded+shares.other-1)<Number.EPSILON*2);
 const zero=stackedAttemptShares(0,0);
 assert.deepEqual(zero,{succeeded:0,other:0});
 assert.deepEqual(stackedAttemptShares(4,5),{succeeded:0,other:0});
});

test('tooltip avoids fabricated percentages for zero or unavailable denominator and marks unresolved cost',()=>{
 const row:ChartDatum={id:'a',label:'alpha',value:1250,attempts:0,succeeded:0};
 const details=detailsByLabel(visualTooltipDetails(row,'knownCostMicrousd',0,undefined,true));
 assert.equal(details['Share of displayed rows'],'Not defined (denominator 0)');
 assert.equal(details['Share of query matches'],'Not supplied');
 assert.equal(details['Success / attempts'],'Not defined (0 attempts)');
 assert.match(details['Cost coverage'],/unresolved charges remain unknown/);
 assert.equal(details['Unresolved cost count'],'Not available at this category level.');
});
