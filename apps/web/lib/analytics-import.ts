export type AnalyticsEvent={
 attemptId:string;
 taskId:string;
 tool:string;
 resource:string;
 startedAt:number;
 settledAt:number|null;
 outcome:string;
 actualCostMicrousd:number|null;
};

/**
 * Class AnalyticsImportError.
 *
 * @extends Error
 *
 * @example
 * ```typescript
 * const instance = new AnalyticsImportError();
 * ```
 */
export class AnalyticsImportError extends Error {
 constructor(message:string){super(message);this.name='AnalyticsImportError';}
}

const FIELDS=['attemptId','taskId','tool','resource','startedAt','settledAt','outcome','actualCostMicrousd'] as const;
const OUTCOMES=new Set(['running','succeeded','failed','unknown','cancelled','not_started','expired_retryable']);
const MAX_BYTES=1024*1024;
const MAX_ROWS=10_000;
const MAX_TEXT=256;
const MAX_EPOCH_SECONDS=253_402_300_799; // 9999-12-31T23:59:59Z

/**
 * Function fail.
 *
 * @param {string} message - Description of message.
 * @returns {never} Description of return value.
 *
 * @example
 * ```typescript
 * const result = fail(...);
 * ```
 */
function fail(message:string):never{throw new AnalyticsImportError(message);}
/**
 * Function record.
 *
 * @param value - Description of value.
 * @returns {value is Record<string,unknown>} Description of return value.
 *
 * @example
 * ```typescript
 * const result = record(...);
 * ```
 */
function record(value:unknown):value is Record<string,unknown>{return value!==null&&typeof value==='object'&&!Array.isArray(value);}
/**
 * Function exactKeys.
 *
 * @param {Record<string,unknown>} value - Description of value.
 * @param {number} rowNumber - Description of rowNumber.
 *
 * @example
 * ```typescript
 * const result = exactKeys(..., ...);
 * ```
 */
function exactKeys(value:Record<string,unknown>,rowNumber:number):void{
 const keys=Object.keys(value);
 if(keys.length!==FIELDS.length||FIELDS.some(key=>!Object.prototype.hasOwnProperty.call(value,key)))fail(`Row ${rowNumber} must contain exactly the eight event fields.`);
}
/**
 * Function textField.
 *
 * @param value - Description of value.
 * @param {string} label - Description of label.
 * @param {number} rowNumber - Description of rowNumber.
 * @returns {string} Description of return value.
 *
 * @example
 * ```typescript
 * const result = textField(..., ..., ...);
 * ```
 */
function textField(value:unknown,label:string,rowNumber:number):string{
 if(typeof value!=='string'||value.length===0||value.trim().length===0||value.length>MAX_TEXT||value.includes('\u0000'))fail(`Row ${rowNumber} has an invalid ${label}.`);
 return value;
}
/**
 * Function timestamp.
 *
 * @param value - Description of value.
 * @param {string} label - Description of label.
 * @param {number} rowNumber - Description of rowNumber.
 * @returns {number} Description of return value.
 *
 * @example
 * ```typescript
 * const result = timestamp(..., ..., ...);
 * ```
 */
function timestamp(value:unknown,label:string,rowNumber:number):number{
 if(typeof value!=='number'||!Number.isFinite(value)||value<0||value>MAX_EPOCH_SECONDS)fail(`Row ${rowNumber} has an invalid ${label}; expected finite epoch seconds from 0 through ${MAX_EPOCH_SECONDS}.`);
 return value;
}
/**
 * Function nullableCost.
 *
 * @param value - Description of value.
 * @param {number} rowNumber - Description of rowNumber.
 * @returns {number|null} Description of return value.
 *
 * @example
 * ```typescript
 * const result = nullableCost(..., ...);
 * ```
 */
function nullableCost(value:unknown,rowNumber:number):number|null{
 if(value===null)return null;
 if(typeof value!=='number'||!Number.isSafeInteger(value)||value<0)fail(`Row ${rowNumber} actualCostMicrousd must be a non-negative safe integer or null.`);
 return value;
}
/**
 * Function normalizeRow.
 *
 * @param value - Description of value.
 * @param {number} rowNumber - Description of rowNumber.
 * @returns {AnalyticsEvent} Description of return value.
 *
 * @example
 * ```typescript
 * const result = normalizeRow(..., ...);
 * ```
 */
function normalizeRow(value:unknown,rowNumber:number):AnalyticsEvent{
 if(!record(value))fail(`Row ${rowNumber} must be an object.`);
 exactKeys(value,rowNumber);
 const attemptId=textField(value.attemptId,'attemptId',rowNumber);
 const taskId=textField(value.taskId,'taskId',rowNumber);
 const tool=textField(value.tool,'tool',rowNumber);
 const resource=textField(value.resource,'resource',rowNumber);
 const startedAt=timestamp(value.startedAt,'startedAt',rowNumber);
 const settledAt=value.settledAt===null?null:timestamp(value.settledAt,'settledAt',rowNumber);
 if(settledAt!==null&&settledAt<startedAt)fail(`Row ${rowNumber} settledAt precedes startedAt.`);
 const outcome=textField(value.outcome,'outcome',rowNumber);
 if(!OUTCOMES.has(outcome))fail(`Row ${rowNumber} has an unsupported execution outcome.`);
 if(outcome==='running'&&settledAt!==null)fail(`Row ${rowNumber} running events must have a null settledAt.`);
 return {attemptId,taskId,tool,resource,startedAt,settledAt,outcome,actualCostMicrousd:nullableCost(value.actualCostMicrousd,rowNumber)};
}

/**
 * Function parseCsv.
 *
 * @param {string} text - Description of text.
 * @returns {unknown[]} Description of return value.
 *
 * @example
 * ```typescript
 * const result = parseCsv(...);
 * ```
 */
function parseCsv(text:string):unknown[]{
 const rows:string[][]=[];
 let row:string[]=[],field='',quoted=false,afterQuote=false,fieldStarted=false;
 const pushField=()=>{row.push(field);field='';afterQuote=false;fieldStarted=false;};
 const pushRow=()=>{pushField();rows.push(row);row=[];if(rows.length>MAX_ROWS+1)fail(`CSV exceeds the ${MAX_ROWS} data-row limit.`);};
 for(let i=0;i<text.length;i++){
  const char=text[i];
  if(quoted){
   if(char==='"'){
    if(text[i+1]==='"'){field+='"';i++;}
    else{quoted=false;afterQuote=true;}
   }else field+=char;
   continue;
  }
  if(afterQuote){
   if(char===','){pushField();continue;}
   if(char==='\n'){pushRow();continue;}
   if(char==='\r'&&text[i+1]==='\n'){pushRow();i++;continue;}
   fail('CSV has characters after a closing quote.');
  }
  if(char==='"'){
   if(fieldStarted||field.length>0)fail('CSV quote appears inside an unquoted field.');
   quoted=true;fieldStarted=true;continue;
  }
  if(char===','){pushField();continue;}
  if(char==='\n'){pushRow();continue;}
  if(char==='\r'){
   if(text[i+1]!=='\n')fail('CSV contains a bare carriage return.');
   pushRow();i++;continue;
  }
  field+=char;fieldStarted=true;
 }
 if(quoted)fail('CSV contains an unterminated quoted field.');
 if(fieldStarted||afterQuote||field.length>0||row.length>0)pushRow();
 if(rows.length===0)fail('CSV is empty.');
 if(rows[0].length!==FIELDS.length||FIELDS.some((fieldName,index)=>rows[0][index]!==fieldName))fail('CSV header must exactly match the required event fields in order.');
 if(rows.length-1>MAX_ROWS)fail(`CSV exceeds the ${MAX_ROWS} data-row limit.`);
 return rows.slice(1).map((cells,index)=>{
  if(cells.length!==FIELDS.length)fail(`CSV row ${index+2} must contain exactly eight fields.`);
  const [attemptId,taskId,tool,resource,startedAt,settledAt,outcome,actualCostMicrousd]=cells;
  return {attemptId,taskId,tool,resource,startedAt:parseCsvNumber(startedAt,'startedAt',index+2),
   settledAt:settledAt===''?null:parseCsvNumber(settledAt,'settledAt',index+2),outcome,
   actualCostMicrousd:actualCostMicrousd===''?null:parseCsvInteger(actualCostMicrousd,'actualCostMicrousd',index+2)};
 });
}
/**
 * Function parseCsvNumber.
 *
 * @param {string} value - Description of value.
 * @param {string} label - Description of label.
 * @param {number} rowNumber - Description of rowNumber.
 * @returns {number} Description of return value.
 *
 * @example
 * ```typescript
 * const result = parseCsvNumber(..., ..., ...);
 * ```
 */
function parseCsvNumber(value:string,label:string,rowNumber:number):number{
 if(!/^(?:0|[0-9]+)(?:\.[0-9]+)?$/.test(value))fail(`CSV row ${rowNumber} has an invalid numeric ${label}.`);
 const parsed=Number(value);
 return timestamp(parsed,label,rowNumber);
}
/**
 * Function parseCsvInteger.
 *
 * @param {string} value - Description of value.
 * @param {string} label - Description of label.
 * @param {number} rowNumber - Description of rowNumber.
 * @returns {number} Description of return value.
 *
 * @example
 * ```typescript
 * const result = parseCsvInteger(..., ..., ...);
 * ```
 */
function parseCsvInteger(value:string,label:string,rowNumber:number):number{
 if(!/^(?:0|[0-9]+)$/.test(value))fail(`CSV row ${rowNumber} has an invalid integer ${label}.`);
 const parsed=Number(value);
 if(!Number.isSafeInteger(parsed)||parsed<0)fail(`CSV row ${rowNumber} ${label} must be a non-negative safe integer.`);
 return parsed;
}

/**
 * Function parseAnalyticsImport.
 *
 * @param {string} text - Description of text.
 * @param {string} filename - Description of filename.
 * @returns {AnalyticsEvent[]} Description of return value.
 *
 * @example
 * ```typescript
 * const result = parseAnalyticsImport(..., ...);
 * ```
 */
export function parseAnalyticsImport(text:string,filename:string):AnalyticsEvent[]{
 if(typeof text!=='string'||typeof filename!=='string')fail('Import requires text and a filename.');
 if(new TextEncoder().encode(text).byteLength>MAX_BYTES)fail(`Import exceeds the ${MAX_BYTES}-byte file limit.`);
 const extension=filename.toLowerCase().split(/[\\/]/).pop()?.split('.').pop();
 let rawRows:unknown[];
 if(extension==='csv')rawRows=parseCsv(text);
 else if(extension==='json'){
  let parsed:unknown;
  try{parsed=JSON.parse(text);}catch{fail('JSON import is malformed.');}
  if(Array.isArray(parsed))rawRows=parsed;
  else if(record(parsed)&&Object.keys(parsed).length===1&&Array.isArray(parsed.rows))rawRows=parsed.rows;
  else fail('JSON import must be an event array or an object containing only a rows array.');
 }else fail('Choose a .csv or .json event file.');
 if(rawRows.length>MAX_ROWS)fail(`Import exceeds the ${MAX_ROWS} data-row limit.`);
 const normalized=rawRows.map((row,index)=>normalizeRow(row,index+1));
 const attemptIds=new Set<string>();
 for(const row of normalized){if(attemptIds.has(row.attemptId))fail(`Duplicate attemptId ${row.attemptId}.`);attemptIds.add(row.attemptId);}
 return normalized;
}

/**
 * Function csvCell.
 *
 * @param {string} value - Description of value.
 * @returns {string} Description of return value.
 *
 * @example
 * ```typescript
 * const result = csvCell(...);
 * ```
 */
function csvCell(value:string):string{
 const safe=/^[\t\r ]*[=+\-@]/.test(value)?`'${value}`:value;
 return /[",\r\n]/.test(safe)?`"${safe.replaceAll('"','""')}"`:safe;
}
/**
 * Function analyticsCSV.
 *
 * @param {Record<string,unknown>[]} rows - Description of rows.
 * @returns {string} Description of return value.
 *
 * @example
 * ```typescript
 * const result = analyticsCSV(...);
 * ```
 */
export function analyticsCSV(rows:Record<string,unknown>[]):string{
 if(!Array.isArray(rows)||rows.length>MAX_ROWS)fail(`CSV export accepts at most ${MAX_ROWS} rows.`);
 const lines=[FIELDS.join(',')];
 for(let index=0;index<rows.length;index++){
  const row=rows[index];
  if(!record(row))fail(`Export row ${index+1} must be an object.`);
  const normalized=normalizeRow(row,index+1);
  const fields=FIELDS.map(key=>{
   const value=normalized[key];
   if(key==='startedAt'||key==='settledAt'||key==='actualCostMicrousd'){
    if(value===null)return '';
    if(typeof value!=='number'||!Number.isFinite(value))fail(`Export row ${index+1} has a non-numeric ${key}.`);
    return String(value);
   }
   if(typeof value!=='string')fail(`Export row ${index+1} has a non-text ${key}.`);
   return csvCell(value);
  });
  lines.push(fields.join(','));
 }
 return `${lines.join('\r\n')}\r\n`;
}
