import type { TrustScore, WorkerSummary, GrantSummary, PolicyViolation } from './types.js';

/**
 * Compute a trust score for an entity based on violations and behavior.
 * Score ranges 0-100, higher is more trustworthy.
 */
export function computeTrustScore(
  entityId: string,
  entityType: TrustScore['entityType'],
  violations: PolicyViolation[],
  workers: WorkerSummary[],
  grants: GrantSummary[]
): TrustScore {
  const factors: TrustScore['factors'] = [];
  let score = 100;

  // Deduct for violations
  const entityViolations = violations.filter(v => v.id.startsWith(entityId));
  for (const v of entityViolations) {
    const penalty = v.severity === 'critical' ? 25 : v.severity === 'warning' ? 10 : 3;
    score -= penalty;
    factors.push({
      label: `${v.severity} violation: ${v.message}`,
      impact: 'negative',
      weight: penalty,
    });
  }

  // Check worker expiry
  if (entityType === 'worker') {
    const worker = workers.find(w => w.workerId === entityId);
    if (worker?.revokedAt) {
      score -= 50;
      factors.push({ label: 'Worker revoked', impact: 'negative', weight: 50 });
    } else if (worker && worker.expiresAt < Date.now()) {
      score -= 20;
      factors.push({ label: 'Worker expired', impact: 'negative', weight: 20 });
    }
  }

  // Check grant budget compliance
  if (entityType === 'grant') {
    const grant = grants.find(g => g.grantId === entityId);
    if (grant) {
      const utilization = grant.maxBudgetMicrousd > 0
        ? (grant.spentMicrousd + grant.reservedMicrousd) / grant.maxBudgetMicrousd
        : 0;
      if (utilization > 1) {
        score -= 30;
        factors.push({ label: 'Budget exceeded', impact: 'negative', weight: 30 });
      } else if (utilization > 0.9) {
        score -= 5;
        factors.push({ label: 'Near budget limit', impact: 'neutral', weight: 5 });
      }
    }
  }

  // Clamp
  score = Math.max(0, Math.min(100, score));

  return {
    entityId,
    entityType,
    score,
    factors,
    lastUpdated: new Date().toISOString(),
  };
}

/**
 * Compute trust scores for all entities in the governance snapshot.
 */
export function computeAllTrustScores(
  violations: PolicyViolation[],
  workers: WorkerSummary[],
  grants: GrantSummary[]
): TrustScore[] {
  const scores: TrustScore[] = [];
  for (const w of workers) {
    scores.push(computeTrustScore(w.workerId, 'worker', violations, workers, grants));
  }
  for (const g of grants) {
    scores.push(computeTrustScore(g.grantId, 'grant', violations, workers, grants));
  }
  return scores;
}
