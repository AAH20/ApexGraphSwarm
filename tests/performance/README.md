# ApexGraphSwarm Performance Test Suite

Performance test suite for ApexGraphSwarm targeting **10,000 RPS** sustained throughput.

## Test Types

| Test Type | Purpose | Duration | Target RPS |
|-----------|---------|----------|------------|
| **Load Test** | Validate behavior under expected production load | ~6 min | 10K RPS |
| **Stress Test** | Find breaking point by pushing beyond target | ~10 min | 10K → 30K RPS |
| **Spike Test** | Validate resilience to sudden traffic bursts | ~6 min | 0 → 10K RPS |
| **Endurance Test** | Detect memory leaks and resource exhaustion | ~30 min | 10K RPS |

## Tools

- **k6** - Modern load testing tool (JavaScript-based)
- **Artillery** - Node.js-based load testing tool

## Prerequisites

### Install k6

```bash
# macOS
brew install k6

# Linux
sudo apt-get install k6

# Docker
docker pull grafana/k6
```

### Install Artillery

```bash
npm install -g artillery
```

### Start the Target Server

```bash
cd apps/web
npm ci
npm run dev
# Server should be running at http://127.0.0.1:3010
```

## Quick Start

### Run All Tests

```bash
cd tests/performance
./run-tests.sh all all
```

### Run Specific Test Type

```bash
# Load test only
./run-tests.sh load k6

# Stress test only
./run-tests.sh stress artillery
```

### Run with Custom Target

```bash
BASE_URL=http://localhost:3010 TARGET_RPS=5000 ./run-tests.sh load k6
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_URL` | `http://127.0.0.1:3010` | Target server URL |
| `TARGET_RPS` | `10000` | Target requests per second |
| `AUTH_TOKEN` | - | Bearer token for protected endpoints |
| `INTEGRATION_TOKEN` | - | Token for integration endpoints |
| `RAMP_UP_DURATION` | `30s` | Ramp-up duration for k6 tests |
| `STEADY_DURATION` | `5m` | Steady-state duration for k6 tests |
| `RAMP_DOWN_DURATION` | `30s` | Ramp-down duration for k6 tests |

## Test Endpoints

### GET Endpoints (No Auth)

- `/api/integrations` - Integration catalog
- `/api/decisions` - Decision providers
- `/api/review` - Review status
- `/api/graph-store` - Graph store status
- `/api/ecosystem/mcp` - MCP discovery catalog

### POST Endpoints (Auth Required)

- `/api/control` - Control operations (status, createFixture, etc.)
- `/api/analytics` - Analytics queries
- `/api/optimization` - Optimization operations

## Pass/Fail Criteria

### Load Test
- p95 latency < 500ms
- p99 latency < 1000ms
- Error rate < 1%
- Sustained RPS ≥ 9,500

### Stress Test
- p95 latency < 1000ms
- p99 latency < 2000ms
- Error rate < 10%
- Graceful degradation (no crashes)

### Spike Test
- p95 latency < 500ms
- p99 latency < 1000ms
- Error rate < 5%
- Recovery within 2 minutes

### Endurance Test
- p95 latency < 500ms
- p99 latency < 1000ms
- Error rate < 1%
- No memory leak indicators
- Stable response times over 30 minutes

## Results

Test results are saved to `tests/performance/results/` in JSON format.

### k6 Results

```bash
# View summary
k6 run --out json=results.json load-test.js

# Generate HTML report
k6 run --out html=report.html load-test.js
```

### Artillery Results

```bash
# View summary
artillery run --output results.json load-test.yml

# Generate HTML report
artillery report results.json
```

## Project Structure

```
tests/performance/
├── config.js                 # Shared k6 configuration
├── run-tests.sh              # Test runner script
├── package.json              # NPM dependencies
├── README.md                 # This file
├── k6/                       # k6 test scripts
│   ├── load-test.js
│   ├── stress-test.js
│   ├── spike-test.js
│   └── endurance-test.js
├── artillery/                # Artillery test scripts
│   ├── load-test.yml
│   ├── stress-test.yml
│   ├── spike-test.yml
│   ├── endurance-test.yml
│   └── artillery-helpers.js
├── fixtures/                 # Test data fixtures
│   └── README.md
└── results/                  # Test output (created at runtime)
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Performance Tests
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm install -g artillery
      - run: |
          wget -q -O - https://github.com/grafana/k6/releases/download/v0.49.0/k6-v0.49.0-linux-amd64.tar.gz | tar xvz
          sudo cp k6-v0.49.0-linux-amd64/k6 /usr/local/bin/
      - run: |
          cd apps/web
          npm ci
          npm run dev &
          sleep 10
      - run: |
          cd tests/performance
          ./run-tests.sh all all
```

## Troubleshooting

### k6 not found

```bash
brew install k6
```

### Artillery not found

```bash
npm install -g artillery
```

### Target not reachable

Ensure the Next.js server is running:

```bash
cd apps/web
npm run dev
```

### High error rates

1. Check server logs for errors
2. Verify auth tokens are correct
3. Reduce target RPS for initial testing
4. Check system resources (CPU, memory)

### Memory leaks detected

1. Review endurance test results for response time drift
2. Check server memory usage during test
3. Profile server with Node.js inspector

## License

Same as ApexGraphSwarm project.
