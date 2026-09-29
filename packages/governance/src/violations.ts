import type { RunStatus, PolicyViolation, GrantSummary, WorkerSummary } from './types.js';

/**
 * Detect policy violations from run status, grants, and workers.
 */
export function detectViolations(
  run: RunStatus,
  grants: GrantSummary[],
  workers: WorkerSummary[]
): PolicyViolation[] {
  const violations: PolicyViolation[] = [];
  let seq = 0;

  // Budget violations
  if (run.run.spentMicrousd > run.run.budgetMicrousd) {
    violations.push({
      id: `violation-${++seq}`,
      severity: 'critical',
      category: 'budget',
      message: `Run ${run.run.id} exceeded budget: ${run.run.spentMicrousd} > ${run.run.budgetMicrousd}`,
      timestamp: new Date().toISOString(),
      details: { spent: run.run.spentMicrousd, budget: run.run.budgetMicrousd },
    });
  }

  // Grant budget violations
  for (const g of grants) {
    if (g.spentMicrousd > g.maxBudgetMicrousd) {
      violations.push({
        id: `violation-${++seq}`,
        severity: 'critical',
        category: 'budget',
        message: `Grant ${g.grantId} exceeded budget: ${g.spentMicrousd} > ${g.maxBudgetMicrousd}`,
        timestamp: new Date().toISOString(),
        details: { grantId: g.grantId, spent: g.spentMicrousd, max: g.maxBudgetMicrousd },
      });
    }
    if (g.revokedAt && g.spentMicrousd > 0) {
      violations.push({
        id: `violation-${++seq}`,
        severity: 'warning',
        category: 'access',
        message: `Revoked grant ${g.grantId} has spend`,
        timestamp: new Date().toISOString(),
        details: { grantId: g.grantId, spent: g.spentMicrousd },
      });
    }
  }

  // Worker violations
  for (const w of workers) {
    if (w.revokedAt) {
      violations.push({
        id: `violation-${++seq}`,
        severity: 'warning',
        category: 'identity',
        message: `Worker ${w.workerId} is revoked`,
        timestamp: new Date().toISOString(),
        details: { workerId: w.workerId },
      });
    }
  }

  // Task-level violations
  for (const task of run.tasks) {
    if (task.attempts >= task.maxAttempts && task.status !== 'completed') {
      violations.push({
        id: `violation-${++seq}`,
        severity: 'warning',
        category: 'capacity',
        message: `Task ${task.taskId} exhausted attempts (${task.attempts}/${task.maxAttempts})`,
        timestamp: new Date().toISOString(),
        details: { taskId: task.taskId, attempts: task.attempts, maxAttempts: task.maxAttempts },
      });
    }
  }

  return violations;
}
