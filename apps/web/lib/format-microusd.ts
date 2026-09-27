/** Exact display for safe integer microUSD; statistical fractional bounds are approximate. */
export function formatMicrousd(value:unknown):string{
 if(typeof value!=='number'||!Number.isFinite(value)||value<0)return 'Unknown';
 if(Number.isSafeInteger(value)){const amount=BigInt(value);return `$${amount/1000000n}.${String(amount%1000000n).padStart(6,'0')}`;}
 if(Number.isInteger(value))return 'Outside browser precision';
 return `≈$${(value/1e6).toFixed(6)}`;
}
