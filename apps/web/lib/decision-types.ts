export type DecisionProvider = 'laya' | 'anyjev';
export type DecisionQuestion = {
  type: 'choice' | 'score' | 'noul';
  instructions: string;
  criteria?: Record<string, string> | string[];
};
export type DecisionInput = {
  providers: DecisionProvider[];
  state: string;
  questions: Record<string, DecisionQuestion>;
  threshold: number;
  maxCostMicrousd: number;
};
export type DecisionAnswer = {
  id: string;
  type: DecisionQuestion['type'];
  value: string | number;
  confidence: number;
  distribution: Record<string, number>;
  reviewRequired: boolean;
};
export type DecisionResult = {
  provider: DecisionProvider;
  status: 'succeeded' | 'failed' | 'unconfigured';
  answers: DecisionAnswer[];
  elapsedMs: number;
  estimatedCostMicrousd: number | null;
  actualCostMicrousd: null;
  model: string | null;
  error?: string;
  warnings: string[];
};
export type ProviderInfo = {
  id: DecisionProvider;
  label: string;
  configured: boolean;
  statusText: string;
  estimatedCostPerQuestionMicrousd: number | null;
};
