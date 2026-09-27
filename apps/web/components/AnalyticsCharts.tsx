'use client';
import {useId,useState} from 'react';
import type {AnalyticsReport} from '@/lib/analytics-types';
import {dollars,decimal} from '@/lib/analytics-types';
import styles from './AnalyticsStudio.module.css';
export function TrendChart({report,metric='cost'}:{report:AnalyticsReport;metric?:'cost'|'attempts'}){
 const [hover,setHover]=useState<number|null>(null),id=useId(),rows=report.daily;
 const values=rows.map(row=>metric==='cost'?row.knownCostMicrousd:row.attempts),max=Math.max(1,...values);
 const point=(value:number,index:number)=>[50+index*700/Math.max(1,rows.length-1),190-value/max*145];
 if(!rows.length)return <p>No dated observations in this window.</p>;
 const selected=rows[Math.min(hover??rows.length-1,rows.length-1)];
 return <div><svg viewBox="0 0 800 230" className={styles.chart} role="img" aria-labelledby={id}><title id={id}>{metric==='cost'?'Known recorded cost':'Attempt count'} by UTC start day. Exact values are in the table below.</title>{[0,.5,1].map(t=><g key={t}><line x1="50" x2="750" y1={190-t*145} y2={190-t*145} stroke="#dde5e7"/><text x="45" y={194-t*145} textAnchor="end" fontSize="10" fill="#66757f">{metric==='cost'?dollars(max*t):Math.round(max*t)}</text></g>)}<polyline points={values.map((v,i)=>point(v,i).join(',')).join(' ')} fill="none" stroke="#237b70" strokeWidth="3"/>{rows.map((row,i)=>{const [x,y]=point(values[i],i);return <circle key={row.date} cx={x} cy={y} r={hover===i?6:3} fill={row.unknownCostRows?'#b77826':'#237b70'}><title>{row.date}: {metric==='cost'?dollars(values[i]):values[i]}{row.unknownCostRows?' · contains unknown cost':''}</title></circle>;})}<text x="50" y="220" fontSize="11" fill="#66757f">{rows[0].date}</text><text x="750" y="220" textAnchor="end" fontSize="11" fill="#66757f">{rows.at(-1)?.date}</text></svg><label className={styles.scrubber}>Inspect a day<input aria-label="Inspect trend day" type="range" min="0" max={rows.length-1} value={hover??rows.length-1} onChange={event=>setHover(Number(event.target.value))}/><output>{selected.date} · {selected.attempts} attempts · {dollars(selected.knownCostMicrousd)} known · {selected.unknownCostRows} costs unknown</output></label></div>;
}
export function Histogram({report}:{report:AnalyticsReport}){
 const rows=report.latency.histogram,max=Math.max(1,...rows.map(row=>row.count));
 return <div className={styles.bars} aria-label="Settled attempt latency histogram">{rows.map(row=><div key={row.label} className={styles.barRow}><span>{row.label}</span><div><span style={{width:`${row.count/max*100}%`}}/></div><strong>{row.count}</strong></div>)}{!rows.length&&<p>No settled durations are available.</p>}</div>;
}
export function ScatterChart({report}:{report:AnalyticsReport}){
 const rows=report.scatter||[],id=useId(),maxX=Math.max(1,...rows.map(p=>p.latencySeconds)),maxY=Math.max(1,...rows.map(p=>p.costMicrousd));
 return <div><svg viewBox="0 0 600 260" className={styles.chart} role="img" aria-labelledby={id}><title id={id}>Settled duration versus known cost, bounded sample. Correlation is descriptive, not causal.</title><line x1="65" y1="210" x2="570" y2="210" stroke="#9caeb5"/><line x1="65" y1="25" x2="65" y2="210" stroke="#9caeb5"/>{rows.map((p,i)=><circle key={i} cx={65+p.latencySeconds/maxX*490} cy={210-p.costMicrousd/maxY*170} r="4" fill="#487daf" opacity=".65"><title>{decimal(p.latencySeconds,'s')} · {dollars(p.costMicrousd)}</title></circle>)}<text x="315" y="248" textAnchor="middle" fontSize="12" fill="#66757f">Duration: 0–{decimal(maxX,' seconds')}</text><text x="68" y="17" fontSize="12" fill="#66757f">Cost: 0–{dollars(maxY)}</text></svg><p>Pearson r: <strong>{decimal(report.correlation.pearsonR)}</strong> · {report.correlation.n} paired observations. Points are a bounded display sample.</p></div>;
}
export function ActivityHeatmap({report}:{report:AnalyticsReport}){
 const days=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],lookup=new Map(report.heatmap.map(cell=>[`${cell.day}:${cell.hour}`,cell.count])),max=Math.max(1,...report.heatmap.map(cell=>cell.count));
 return <div className={styles.heatScroll}><div className={styles.heatmap} role="img" aria-label="Activity by UTC weekday and hour; darker squares indicate more attempts"><span/>{Array.from({length:24},(_,hour)=><small key={hour}>{hour%3===0?hour:''}</small>)}{days.map((day,index)=><div className={styles.heatRow} key={day}><small>{day}</small>{Array.from({length:24},(_,hour)=>{const count=lookup.get(`${index}:${hour}`)||0;return <span key={hour} title={`${day} ${hour}:00 UTC: ${count} attempts`} style={{backgroundColor:`rgba(35,123,112,${.06+.94*count/max})`}}/>;})}</div>)}</div><p>UTC start times · {max} attempts in the busiest hour cell. Hover for counts.</p><details><summary>Accessible activity counts</summary><ul>{report.heatmap.map(cell=><li key={`${cell.day}:${cell.hour}`}>{days[cell.day]} {cell.hour}:00 UTC: {cell.count}</li>)}</ul></details></div>;
}
export function ForecastChart({report}:{report:AnalyticsReport}){
 const rows=report.forecast.points,id=useId(),max=Math.max(1,...rows.map(row=>row.upperMicrousd));
 if(!rows.length)return <p className={styles.empty}>Forecast withheld: {report.forecast.status}. Add sufficient complete daily cost history before using a predictive estimate.</p>;
 const x=(i:number)=>60+i*680/Math.max(1,rows.length-1),y=(v:number)=>190-v/max*150;
 return <><svg viewBox="0 0 800 235" className={styles.chart} role="img" aria-labelledby={id}><title id={id}>Seven-day baseline spending forecast with heuristic error envelope, not a confidence interval.</title><polygon points={[...rows.map((r,i)=>`${x(i)},${y(r.upperMicrousd)}`),...rows.map((r,i)=>`${x(i)},${y(r.lowerMicrousd)}`).reverse()].join(' ')} fill="#e2ebf5"/><polyline points={rows.map((r,i)=>`${x(i)},${y(r.predictedMicrousd)}`).join(' ')} fill="none" stroke="#487daf" strokeWidth="3" strokeDasharray="7 4"/>{rows.map((r,i)=><g key={r.date}><circle cx={x(i)} cy={y(r.predictedMicrousd)} r="4" fill="#487daf"/><text x={x(i)} y="220" textAnchor="middle" fontSize="11" fill="#66757f">{r.date.slice(5)}</text></g>)}</svg><p>The shaded envelope describes a heuristic error range; it is not a calibrated probability or confidence interval.</p></>;
}
