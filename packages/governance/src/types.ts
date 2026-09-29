// Governance domain types extracted from the ApexGraphSwarm control plane

export type RunStatus = {
  run: {
    id: string;
    status: string;
    version: number;
    budgetMicrousd: number;
    reservedMicrousd: number;
    spentMicrousd: number;
    remainingMicrousd: number;
    cancelRequested: boolean;
  };
  agents: { id: string; name: string }[];
  tasks: TaskSummary[];
  events: EventSummary[];
};

export type TaskSummary = {
  taskId: string;
  id: string;
  agentId: string;
  status: string;
  dependencies: string[];
  attempts: number;
  maxAttempts: number;
  actualCostMicrousd: number | null;
  executionClass: string;
  requireResourceCapacity?: boolean;
  reservedCostMicrousd?: number;
  workerId?: string | null;
  leaseExpiresAt?: number | null;
  completedAt?: number | null;
  payload?: { sourceTaskId?: string; execution?: { version?: number } };
};

export type EventSummary = {
  sequence: number;
  type: string;
  at: string;
  taskId?: string;
};

export type GrantSummary = {
  grantId: string;
  principalId: string;
  toolId: string;
  resourceId: string;
  maxBudgetMicrousd: number;
  spentMicrousd: number;
  reservedMicrousd: number;
  expiresAt: number;
  revokedAt: number | null;
};

export type WorkerSummary = {
  workerId: string;
  principalId: string;
  expiresAt: number;
  revokedAt: number | null;
};

export type PolicyViolation = {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  category: 'budget' | 'access' | 'identity' | 'capacity' | 'reconciliation';
  message: string;
  timestamp: string;
  details?: Record<string, unknown>;
};

export type TrustScore = {
  entityId: string;
  entityType: 'worker' | 'principal' | 'agent' | 'grant';
  score: number;
  factors: { label: string; impact: 'positive' | 'negative' | 'neutral'; weight: number }[];
  lastUpdated: string;
};

export type GovernanceSnapshot = {
  run: RunStatus;
  grants: GrantSummary[];
  workers: WorkerSummary[];
  violations: PolicyViolation[];
  trustScores: TrustScore[];
};
