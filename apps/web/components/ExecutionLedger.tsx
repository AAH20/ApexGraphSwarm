import {formatMicrousd} from '@/lib/format-microusd';
/**
 * Type LedgerView.
 *
 *
 * @example
 * ```typescript
 * import { LedgerView } from './module';
 * ```
 */
export type LedgerView={totalAttempts:number;returnedAttempts:number;truncated:boolean;knownActualMicrousd:number;unresolvedCostCount:number;coverageComplete:boolean;allCostsResolved:boolean;attempts:{attemptId:string;taskId:string;attempt:number;workerId:string;principalId:string|null;grantId:string|null;reservedMicrousd:number;startedAt:number;settledAt:number|null;outcome:string;actualCostMicrousd:number|null;receipt:unknown}[]};
/**
 * React component ExecutionLedger.
 *
 * @param {{ledger} ledger - Description of ledger.
 *
 * @example
 * ```typescript
 * const result = ExecutionLedger(...);
 * ```
 */
export default function ExecutionLedger({ledger}:{ledger:LedgerView}){
 return <section aria-label="Execution and cost ledger"><h3>Attributable execution ledger</h3><div className="apex-metrics"><div><strong>{ledger.totalAttempts}</strong><span>Recorded attempts, including retries</span></div><div><strong>{formatMicrousd(ledger.knownActualMicrousd)}</strong><span>Known settled cost</span></div><div><strong>{ledger.unresolvedCostCount}</strong><span>Attempts with unresolved cost</span></div><div><strong>{ledger.coverageComplete?'Complete':'Incomplete'}</strong><span>Attempt record coverage</span></div></div><p className="apex-note">Known settled cost is not a total while costs remain unresolved. Historical tasks may lack attempt records. Receipts record worker assertions; provider invoice reconciliation is a separate step.</p>{ledger.truncated&&<p>Showing the latest {ledger.returnedAttempts} of {ledger.totalAttempts} attempts. Use the Python ledger API for a larger bounded page.</p>}<div className="apex-table-wrap"><table><thead><tr><th>Task / attempt</th><th>Outcome</th><th>Principal / worker</th><th>Grant</th><th>Reserved</th><th>Actual</th><th>Receipt evidence</th></tr></thead><tbody>{ledger.attempts.map(attempt=><tr key={attempt.attemptId}><td>{attempt.taskId.slice(0,12)} / {attempt.attempt}</td><td>{attempt.outcome}</td><td>{attempt.principalId||'Fixture'} / {attempt.workerId}</td><td>{attempt.grantId?.slice(0,12)||'None'}</td><td>{formatMicrousd(attempt.reservedMicrousd)}</td><td>{formatMicrousd(attempt.actualCostMicrousd)}</td><td><details><summary>Inspect</summary><pre className="apex-json">{JSON.stringify(attempt,null,2)}</pre></details></td></tr>)}</tbody></table></div></section>;
}
