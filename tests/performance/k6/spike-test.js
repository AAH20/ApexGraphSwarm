/**
 * k6 Spike Test - Sudden burst to 10K RPS.
 * Validates system resilience to traffic spikes.
 */
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';
import {
  BASE_URL,
  TARGET_RPS,
  AUTH_HEADERS,
  JSON_HEADERS,
} from './config.js';

// Custom metrics
const errorRate = new Rate('errors');
const spikeRecovery = new Trend('spike_recovery', true);

export const options = {
  scenarios: {
    spike_test: {
      executor: 'ramping-arrival-rate',
      startRate: 0,
      timeUnit: '1s',
      preAllocatedVUs: 2000,
      maxVUs: 5000,
      stages: [
        // Baseline
        { duration: '30s', target: Math.floor(TARGET_RPS * 0.1) },
        // Sudden spike to full target
        { duration: '10s', target: TARGET_RPS },
        // Sustained spike
        { duration: '2m', target: TARGET_RPS },
        // Drop back to baseline
        { duration: '10s', target: Math.floor(TARGET_RPS * 0.1) },
        // Recovery observation
        { duration: '2m', target: Math.floor(TARGET_RPS * 0.1) },
        // Second spike (smaller)
        { duration: '10s', target: Math.floor(TARGET_RPS * 0.5) },
        { duration: '1m', target: Math.floor(TARGET_RPS * 0.5) },
        // Final recovery
        { duration: '10s', target: 0 },
      ],
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.05'],
    errors: ['rate<0.10'],
  },
};

const endpoints = [
  { weight: 35, fn: () => http.get(`${BASE_URL}/api/integrations`, { headers: JSON_HEADERS }) },
  { weight: 25, fn: () => http.get(`${BASE_URL}/api/decisions`, { headers: JSON_HEADERS }) },
  { weight: 20, fn: () => http.get(`${BASE_URL}/api/ecosystem/mcp`, { headers: JSON_HEADERS }) },
  { weight: 10, fn: () => http.get(`${BASE_URL}/api/review`, { headers: JSON_HEADERS }) },
  { weight: 10, fn: () => http.post(`${BASE_URL}/api/control`, JSON.stringify({ action: 'status', runId: 'spike-test' }), { headers: AUTH_HEADERS }) },
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

  spikeRecovery.add(duration);

  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });

  errorRate.add(!success);
  sleep(0.001);
}
