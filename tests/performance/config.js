/**
 * Shared k6 configuration for ApexGraphSwarm performance tests.
 * Target: 10K RPS sustained.
 */

export const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:3010';
export const TARGET_RPS = parseInt(__ENV.TARGET_RPS || '10000', 10);
export const RAMP_UP_DURATION = __ENV.RAMP_UP_DURATION || '30s';
export const STEADY_DURATION = __ENV.STEADY_DURATION || '5m';
export const RAMP_DOWN_DURATION = __ENV.RAMP_DOWN_DURATION || '30s';

// Auth token for protected endpoints (set via environment)
export const AUTH_TOKEN = __ENV.AUTH_TOKEN || '';
export const INTEGRATION_TOKEN = __ENV.INTEGRATION_TOKEN || '';

// Common headers
export const JSON_HEADERS = {
  'Content-Type': 'application/json',
};

export const AUTH_HEADERS = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${AUTH_TOKEN}`,
};

export const INTEGRATION_HEADERS = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${INTEGRATION_TOKEN}`,
};

// Threshold definitions for pass/fail criteria
export const THRESHOLDS = {
  http_req_duration: ['p(95)<500', 'p(99)<1000'],
  http_req_failed: ['rate<0.01'],
  http_reqs: [`rate>=${TARGET_RPS * 0.95}`],
};

// Scenario definitions for different test types
export const SCENARIOS = {
  // Lightweight GET endpoints (no auth required)
  light: {
    executor: 'constant-arrival-rate',
    rate: Math.ceil(TARGET_RPS * 0.6),
    timeUnit: '1s',
    duration: STEADY_DURATION,
    preAllocatedVUs: 500,
    maxVUs: 2000,
  },
  // Medium POST endpoints (auth required)
  medium: {
    executor: 'constant-arrival-rate',
    rate: Math.ceil(TARGET_RPS * 0.3),
    timeUnit: '1s',
    duration: STEADY_DURATION,
    preAllocatedVUs: 300,
    maxVUs: 1500,
  },
  // Heavy endpoints (complex operations)
  heavy: {
    executor: 'constant-arrival-rate',
    rate: Math.ceil(TARGET_RPS * 0.1),
    timeUnit: '1s',
    duration: STEADY_DURATION,
    preAllocatedVUs: 100,
    maxVUs: 500,
  },
};

// Endpoint definitions
export const ENDPOINTS = {
  // GET endpoints (no auth)
  integrations: {
    method: 'GET',
    path: '/api/integrations',
    headers: JSON_HEADERS,
    weight: 30,
  },
  decisions: {
    method: 'GET',
    path: '/api/decisions',
    headers: JSON_HEADERS,
    weight: 20,
  },
  reviewStatus: {
    method: 'GET',
    path: '/api/review',
    headers: JSON_HEADERS,
    weight: 15,
  },
  graphStoreStatus: {
    method: 'GET',
    path: '/api/graph-store',
    headers: JSON_HEADERS,
    weight: 15,
  },
  mcpCatalog: {
    method: 'GET',
    path: '/api/ecosystem/mcp',
    headers: JSON_HEADERS,
    weight: 20,
  },
  // POST endpoints (auth required)
  controlStatus: {
    method: 'POST',
    path: '/api/control',
    headers: AUTH_HEADERS,
    body: JSON.stringify({ action: 'status', runId: 'perf-test-run' }),
    weight: 50,
  },
  analyticsQuery: {
    method: 'POST',
    path: '/api/analytics',
    headers: AUTH_HEADERS,
    body: JSON.stringify({ source: 'live', days: 7, tool: 'test', rows: [] }),
    weight: 30,
  },
  optimizationAction: {
    method: 'POST',
    path: '/api/optimization',
    headers: AUTH_HEADERS,
    body: JSON.stringify({ action: 'hierarchy' }),
    weight: 20,
  },
};
