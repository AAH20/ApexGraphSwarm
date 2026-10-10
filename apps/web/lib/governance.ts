// Re-export governance types from the shared package
// This file provides backward compatibility for existing imports
export type {
  RunStatus,
  TaskSummary,
  EventSummary,
  GrantSummary,
  WorkerSummary,
  PolicyViolation,
  TrustScore,
  GovernanceSnapshot,
} from '@apexgraphswarm/governance';

export {
  computeTrustScore,
  computeAllTrustScores,
  detectViolations,
} from '@apexgraphswarm/governance';
