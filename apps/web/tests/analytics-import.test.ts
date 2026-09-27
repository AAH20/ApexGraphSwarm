import assert from 'node:assert/strict';
import test from 'node:test';
import {AnalyticsImportError,analyticsCSV,parseAnalyticsImport,type AnalyticsEvent} from '../lib/analytics-import';

const header='attemptId,taskId,tool,resource,startedAt,settledAt,outcome,actualCostMicrousd';
const event:AnalyticsEvent={attemptId:'attempt-1',taskId:'task-1',tool:'integration:openrouter:review',resource:'model:reviewer',startedAt:1700000000.25,settledAt:1700000002.5,outcome:'succeeded',actualCostMicrousd:0};
const row=(changes:Partial<AnalyticsEvent>={}):AnalyticsEvent=>({...event,...changes});
const json=(items:unknown[])=>JSON.stringify({rows:items});
const rejectsImport=(text:string,filename='events.json',pattern?:RegExp)=>{
 assert.throws(()=>parseAnalyticsImport(text,filename),error=>error instanceof AnalyticsImportError&&(!pattern||pattern.test(error.message)));
};

test('JSON array and rows wrapper preserve exact values and unknown cost as null',()=>{
 const unknown=row({attemptId:'attempt-unknown',outcome:'unknown',actualCostMicrousd:null});
 assert.deepEqual(parseAnalyticsImport(JSON.stringify([event,unknown]),'events.JSON'),[event,unknown]);
 assert.equal(parseAnalyticsImport(json([unknown]),'folder/events.json')[0].actualCostMicrousd,null);
 assert.equal(parseAnalyticsImport(json([event]),'events.json')[0].actualCostMicrousd,0);
});

test('CSV parser handles RFC quoted commas, CRLF, escaped quotes, and embedded newlines',()=>{
 const csv=[header,
  '"attempt,quoted","task\ncontinued","tool ""review""",resource,1700000000.25,1700000002.5,succeeded,19',
 ].join('\r\n')+'\r\n';
 const [parsed]=parseAnalyticsImport(csv,'events.csv');
 assert.equal(parsed.attemptId,'attempt,quoted');
 assert.equal(parsed.taskId,'task\ncontinued');
 assert.equal(parsed.tool,'tool "review"');
 assert.equal(parsed.actualCostMicrousd,19);
});

test('unknown CSV prices stay blank/null and export neutralizes spreadsheet formulas',()=>{
 const unsafe=row({attemptId:'=SUM(1,2)',taskId:'  +cmd|x',tool:'@unsafe',resource:'resource\nsecond line',outcome:'failed',actualCostMicrousd:null});
 const csv=analyticsCSV([unsafe]);
 assert.match(csv,/^attemptId,taskId,tool,resource,/);
 assert.match(csv,/"'=SUM\(1,2\)"/);
 assert.ok(csv.includes(",'  +cmd|x,'@unsafe,"));
 assert.match(csv,/"resource\nsecond line"/);
 assert.match(csv,/failed,$/m);
 const [parsed]=parseAnalyticsImport(csv,'safe.csv');
 assert.equal(parsed.attemptId,"'=SUM(1,2)");
 assert.equal(parsed.taskId,"'  +cmd|x");
 assert.equal(parsed.tool,"'@unsafe");
 assert.equal(parsed.actualCostMicrousd,null);
});

test('rejects malformed CSV quoting, bare carriage returns, and nonexact headers',()=>{
 rejectsImport(`${header}\r\n"unterminated,x`, 'events.csv',/unterminated/);
 rejectsImport(`${header}\r\nattempt-1,task-1,tool,resource,1,2,succeeded,3"tail\r\n`,'events.csv',/closing quote|inside an unquoted/);
 rejectsImport(`${header}\r\nattempt-1,task-1,tool,resource,1,2,succeeded,3\r`,'events.csv',/bare carriage/);
 rejectsImport(`${header.replace('tool','toolName')}\r\n`,'events.csv',/header/);
});

test('rejects duplicate attempts, unexpected fields, and malformed root shape',()=>{
 rejectsImport(json([event,{...event}]),'events.json',/Duplicate attemptId/);
 rejectsImport(JSON.stringify([{...event,extra:'not accepted'}]),'events.json',/exactly the eight/);
 rejectsImport(JSON.stringify({rows:[event],metadata:{source:'x'}}),'events.json',/object containing only/);
 rejectsImport(JSON.stringify({items:[event]}),'events.json',/object containing only/);
 rejectsImport('[]','events.txt',/Choose a .csv or .json/);
});

test('checks safe integer prices, bounded timestamps, ordering, and ledger outcomes',()=>{
 rejectsImport(JSON.stringify([{...event,actualCostMicrousd:Number.MAX_SAFE_INTEGER+1}]),'events.json',/safe integer/);
 rejectsImport(JSON.stringify([{...event,actualCostMicrousd:1.5}]),'events.json',/safe integer/);
 rejectsImport('[{"attemptId":"a","taskId":"t","tool":"x","resource":"r","startedAt":1e999,"settledAt":null,"outcome":"running","actualCostMicrousd":null}]','events.json',/startedAt/);
 rejectsImport(JSON.stringify([{...event,startedAt:-1}]),'events.json',/startedAt/);
 rejectsImport(JSON.stringify([{...event,startedAt:253402300800}]),'events.json',/startedAt/);
 rejectsImport(JSON.stringify([{...event,settledAt:event.startedAt-1}]),'events.json',/precedes/);
 rejectsImport(JSON.stringify([{...event,outcome:'invented'}]),'events.json',/unsupported execution outcome/);
 assert.equal(parseAnalyticsImport(JSON.stringify([{...event,outcome:'running',settledAt:null}]),'events.json')[0].settledAt,null);
 rejectsImport(JSON.stringify([{...event,outcome:'running',settledAt:event.startedAt}]),'events.json',/running events must have a null/);
});

test('enforces UTF-8 file and row count bounds before accepting events',()=>{
 rejectsImport(`${header}\r\n`+'x'.repeat(1024*1024),'events.csv',/1 MiB|1048576-byte/);
 const tooMany=[header,...Array.from({length:10001},(_,index)=>`attempt-${index},task,tool,resource,1,,running,`)].join('\r\n');
 rejectsImport(tooMany,'events.csv',/10000 data-row/);
});
