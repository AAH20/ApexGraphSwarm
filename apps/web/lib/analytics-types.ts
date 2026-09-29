import {formatMicrousd} from './format-microusd';
export type AnalyticsReport={
 version:number;source:string;generatedAt:string;windowStart:string;
 quality:{scannedRows:number;selectedRows:number;unknownCostRows:number;invalidRows:number;truncated:boolean;[key:string]:unknown};
 kpis:{attempts:number;succeeded:number;failed:number;running:number;knownCostMicrousd:number;costPerSuccessMicrousd:number|null;successRate:number|null};
 latency:{count:number;p50:number|null;p95:number|null;mean:number|null;stddev:number|null;histogram:{label:string;count:number}[];sampled:boolean};
 daily:{date:string;attempts:number;succeeded:number;knownCostMicrousd:number;unknownCostRows:number}[];
 cohorts:{tool:string;resource:string;attempts:number;succeeded:number;knownCostMicrousd:number;unknownCostRows:number;meanLatencySeconds:number|null}[];
 heatmap:{day:number;hour:number;count:number}[];
 graph:{nodes:{id:string;label:string;kind:string}[];edges:{source:string;target:string;attempts:number;knownCostMicrousd:number}[]};
 forecast:{status:string;points:{date:string;predictedMicrousd:number;lowerMicrousd:number;upperMicrousd:number}[];backtestMAE:number|null;naiveMAE:number|null;method:string;limitations:string[]};
 anomalies:{date:string;value:number;reason:string}[];correlation:{n:number;pearsonR:number|null};scatter:{latencySeconds:number;costMicrousd:number}[];limitations:string[];availableTools:string[];
};
/**
 * Function dollars.
 *
 * @param {number|null|undefined} micro - Description of micro.
 *
 * @example
 * ```typescript
 * const result = dollars(...);
 * ```
 */
/**
 * Constant dollars.
 *
 *
 * @example
 * ```typescript
 * import { dollars } from './module';
 * ```
 */
export const dollars=(micro:number|null|undefined)=>formatMicrousd(micro??null);
/**
 * Function decimal.
 *
 * @param {number|null|undefined} value - Description of value.
 * @param suffix - Description of suffix.
 *
 * @example
 * ```typescript
 * const result = decimal(..., ...);
 * ```
 */
/**
 * Constant decimal.
 *
 *
 * @example
 * ```typescript
 * import { decimal } from './module';
 * ```
 */
export const decimal=(value:number|null|undefined,suffix='')=>value==null?'Insufficient data':`${new Intl.NumberFormat('en-US',{maximumFractionDigits:2}).format(value)}${suffix}`;
