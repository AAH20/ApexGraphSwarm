/**
 * k6 Load Test - Gradual ramp to 10K RPS target.
 * Validates system behavior under expected production load.
 */
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';
import {
  BASE_URL,
  TARGET_RPS,
  RAMP_UP_DURATION,
  STEADY_DURATION,
  RAMP_DOWN_DURATION,
  AUTH_HEADERS,
  JSON_HEADERS,
} from './config.js';

// Custom metrics
const errorRate = new Rate('errors');
const endpointLatency = new Trend('endpoint_latency', true);

export const options = {
  scenarios: {
    load_test: {
      executor: 'ramping-arrival-rate',
      startRate: 0,
      timeUnit: '1s',
      preAllocatedVUs: 500,
      maxVUs: 3000,
      stages: [
        { duration: RAMP_UP_DURATION, target: TARGET_RPS },
        { duration: STEADY_DURATION, target: TARGET_RPS },
        { duration: RAMP_DOWN_DURATION, target: 0 },
      ],
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.01'],
    errors: ['rate<0.05'],
  },
};

// Weighted endpoint selection
const endpoints = [
  { weight: 25, fn: () => http.get(`${BASE_URL}/api/integrations`, { headers: JSON_HEADERS }) },
  { weight: 20, fn: () => http.get(`${BASE_URL}/api/decisions`, { headers: JSON_HEADERS }) },
  { weight: 15, fn: () => http.get(`${BASE_URL}/api/review`, { headers: JSON_HEADERS }) },
  { weight: 15, fn: () => http.get(`${BASE_URL}/api/graph-store`, { headers: JSON_HEADERS }) },
  { weight: 15, fn: () => http.get(`${BASE_URL}/api/ecosystem/mcp`, { headers: JSON_HEADERS }) },
  { weight: 10, fn: () => http.post(`${BASE_URL}/api/control`, JSON.stringify({ action: 'status', runId: 'load-test' }), { headers: AUTH_HEADERS }) },
];

const totalWeight = endpoints.reduce((sum, ep) => sum + ep.weight, 0);

function selectEndpoint() {
  let random = Math.random() * totalWeight;
  for (const ep of endpoints) {
    random -= ep.weight;
    if (random <= 0) return ep.fn();
  }
  return endpoints[0].fn();
}

export default function () {
  const start = Date.now();
  const response = selectEndpoint();
  const duration = Date.now() - start;

  endpointLatency.add(duration);

  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });

  errorRate.add(!success);

  // Minimal sleep to prevent overwhelming the system
  sleep(0.001);
}
