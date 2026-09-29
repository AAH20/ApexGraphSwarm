import {dollars} from './analytics-types';
import type {AnalyticsMetric, ChartDatum} from './analytics-visuals';

/**
 * Type ChartTooltipDetail.
 *
 *
 * @example
 * ```typescript
 * import { ChartTooltipDetail } from './module';
 * ```
 */
export type ChartTooltipDetail = {label: string; value: string};
/**
 * Core library module for chart tooltip details.ts functionality.
 *
 * @module chart-tooltip-details
 * @packageDocumentation
 */
const metricName=(metric:AnalyticsMetric)=>metric==='knownCostMicrousd'?'known recorded cost':metric==='succeeded'?'successful attempts':'attempts';
const format=(value:number,metric:AnalyticsMetric)=>metric==='knownCostMicrousd'?dollars(value):new Intl.NumberFormat('en-US',{maximumFractionDigits:0}).format(value);

/**
 * Function percentShare.
 *
 * @param {number} value - Description of value.
 * @param {number|undefined} denominator - Description of denominator.
 * @param {AnalyticsMetric} metric - Description of metric.
 * @returns {string} Description of return value.
 *
 * @example
 * ```typescript
 * const result = percentShare(..., ..., ...);
 * ```
 */
export function percentShare(value:number,denominator:number|undefined,metric:AnalyticsMetric='attempts'):string{return denominator===undefined?'Not supplied':denominator===0?'Not defined (denominator 0)':`${(100*value/denominator).toFixed(1)}% (${format(value,metric)} / ${format(denominator,metric)})`;}

/**
 * Function visualTooltipDetails.
 *
 * @param {ChartDatum} row - Description of row.
 * @param {AnalyticsMetric} metric - Description of metric.
 * @param {number} displayedTotal - Description of displayedTotal.
 * @param {number} filteredTotal - Description of filteredTotal.
 * @param partial - Description of partial.
 * @param {ChartTooltipDetail[]} extras - Description of extras.
 * @returns {ChartTooltipDetail[]} Description of return value.
 *
 * @example
 * ```typescript
 * const result = visualTooltipDetails(..., ..., ..., ..., ..., ...);
 * ```
 */
export function visualTooltipDetails(row:ChartDatum,metric:AnalyticsMetric,displayedTotal:number,filteredTotal?:number,partial=false,extras:ChartTooltipDetail[]=[]):ChartTooltipDetail[]{
 const other=row.attempts-row.succeeded;
 const rate=row.attempts===0?'Not defined (0 attempts)':`${(100*row.succeeded/row.attempts).toFixed(1)}% (${format(row.succeeded,'attempts')} / ${format(row.attempts,'attempts')})`;
 const details:ChartTooltipDetail[]=[
  {label:'Category',value:row.label},
  {label:metricName(metric),value:format(row.value,metric)},
  {label:'Share of displayed rows',value:percentShare(row.value,displayedTotal,metric)},
  {label:'Share of query matches',value:percentShare(row.value,filteredTotal,metric)},
  {label:'Attempts',value:format(row.attempts,'attempts')},
  {label:'Succeeded',value:format(row.succeeded,'attempts')},
  {label:'Other attempts',value:format(other,'attempts')},
  {label:'Success / attempts',value:rate},
 ];
 if(metric==='knownCostMicrousd')details.push({label:'Cost coverage',value:partial?'Partial evidence; unresolved charges remain unknown and are not zero.':'Recorded known-cost total; source completeness is described with the chart.'},{label:'Unresolved cost count',value:'Not available at this category level.'});
 details.push(...extras);
 return details;
}

export function stackedAttemptShares(attempts:number,succeeded:number):{succeeded:number;other:number}{
 if(!Number.isSafeInteger(attempts)||attempts<=0||!Number.isSafeInteger(succeeded)||succeeded<0||succeeded>attempts)return {succeeded:0,other:0};
 const success=succeeded/attempts;
 return {succeeded:success,other:(attempts-succeeded)/attempts};
}
