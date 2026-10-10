/**
 * k6 Stress Test - Push beyond 10K RPS to find breaking point.
 * Identifies system limits and degradation patterns.
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
const saturationPoint = new Trend('saturation_point', true);

export const options = {
  scenarios: {
    stress_test: {
      executor: 'ramping-arrival-rate',
      startRate: TARGET_RPS,
      timeUnit: '1s',
      preAllocatedVUs: 1000,
      maxVUs: 5000,
      stages: [
        // Start at target and push beyond
        { duration: '1m', target: TARGET_RPS },
        { duration: '1m', target: Math.floor(TARGET_RPS * 1.25) },
        { duration: '1m', target: Math.floor(TARGET_RPS * 1.5) },
        { duration: '1m', target: Math.floor(TARGET_RPS * 1.75) },
        { duration: '1m', target: TARGET_RPS * 2 },
        { duration: '1m', target: Math.floor(TARGET_RPS * 2.5) },
        { duration: '1m', target: TARGET_RPS * 3 },
        // Recovery phase
        { duration: '2m', target: TARGET_RPS },
        { duration: '1m', target: 0 },
      ],
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<1000', 'p(99)<2000'],
    http_req_failed: ['rate<0.10'],
    errors: ['rate<0.15'],
  },
};

// Focus on read-heavy mix for stress testing
const endpoints = [
  { weight: 40, fn: () => http.get(`${BASE_URL}/api/integrations`, { headers: JSON_HEADERS }) },
  { weight: 30, fn: () => http.get(`${BASE_URL}/api/decisions`, { headers: JSON_HEADERS }) },
  { weight: 20, fn: () => http.get(`${BASE_URL}/api/ecosystem/mcp`, { headers: JSON_HEADERS }) },
  { weight: 10, fn: () => http.post(`${BASE_URL}/api/control`, JSON.stringify({ action: 'status', runId: 'stress-test' }), { headers: AUTH_HEADERS }) },
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

  saturationPoint.add(duration);

  const success = check(response, {
    'status is 200 or 429': (r) => r.status === 200 || r.status === 429,
    'response time < 1000ms': (r) => r.timings.duration < 1000,
  });

  errorRate.add(!success);
  sleep(0.001);
}
