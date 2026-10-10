// Browser JSON numbers must not silently round integer microUSD amounts.
/**
 * Function assertJsonPrecision.
 *
 * @param value - Description of value.
 *
 * @example
 * ```typescript
 * const result = assertJsonPrecision(...);
 * ```
 */
export function assertJsonPrecision(value:unknown):void {
 const pending:unknown[]=[value];let count=0;
 while(pending.length){
  if(++count>100000)throw Error('Experiment JSON exceeds 100,000 values.');
  const item=pending.pop();
  if(typeof item==='number'&&(!Number.isFinite(item)||(Number.isInteger(item)&&!Number.isSafeInteger(item))))throw Error('A numeric value exceeds browser JSON precision. Use the Python interface for larger exact integers.');
  if(Array.isArray(item)){for(const child of item)pending.push(child);}
  else if(item&&typeof item==='object'){for(const child of Object.values(item))pending.push(child);}
 }
}
