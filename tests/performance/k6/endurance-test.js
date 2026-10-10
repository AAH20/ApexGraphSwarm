/**
 * k6 Endurance Test - Sustained 10K RPS for extended period.
 * Validates system stability, memory leaks, and resource exhaustion.
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
const memoryLeakIndicator = new Trend('memory_leak_indicator', true);
const responseTimeDrift = new Trend('response_time_drift', true);

export const options = {
  scenarios: {
    endurance_test: {
      executor: 'constant-arrival-rate',
      rate: TARGET_RPS,
      timeUnit: '1s',
      duration: '30m',
      preAllocatedVUs: 1000,
      maxVUs: 3000,
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.01'],
    errors: ['rate<0.05'],
  },
};

const endpoints = [
  { weight: 30, fn: () => http.get(`${BASE_URL}/api/integrations`, { headers: JSON_HEADERS }) },
  { weight: 25, fn: () => http.get(`${BASE_URL}/api/decisions`, { headers: JSON_HEADERS }) },
  { weight: 20, fn: () => http.get(`${BASE_URL}/api/ecosystem/mcp`, { headers: JSON_HEADERS }) },
  { weight: 15, fn: () => http.get(`${BASE_URL}/api/review`, { headers: JSON_HEADERS }) },
  { weight: 10, fn: () => http.post(`${BASE_URL}/api/control`, JSON.stringify({ action: 'status', runId: 'endurance-test' }), { headers: AUTH_HEADERS }) },
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

let iterationCount = 0;

export default function () {
  iterationCount++;
  const start = Date.now();
  const response = selectEndpoint();
  const duration = Date.now() - start;

  // Track response time drift over time (every 1000 iterations)
  if (iterationCount % 1000 === 0) {
    responseTimeDrift.add(duration);
  }

  // Memory leak indicator: track if response times increase over time
  memoryLeakIndicator.add(duration);

  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });

  errorRate.add(!success);
  sleep(0.001);
}
