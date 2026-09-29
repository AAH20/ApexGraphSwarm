# Performance Test Fixtures
# Sample data for ApexGraphSwarm performance tests

## Control Run Fixtures

### Small Run (1 agent)
```json
{
  "action": "createFixture",
  "agents": 1,
  "idempotencyKey": "perf-test-small-001"
}
```

### Medium Run (10 agents)
```json
{
  "action": "createFixture",
  "agents": 10,
  "idempotencyKey": "perf-test-medium-001"
}
```

### Large Run (100 agents)
```json
{
  "action": "createFixture",
  "agents": 100,
  "idempotencyKey": "perf-test-large-001"
}
```

## Analytics Query Fixtures

### Daily Summary
```json
{
  "source": "live",
  "days": 1,
  "tool": "performance-test",
  "rows": []
}
```

### Weekly Summary
```json
{
  "source": "live",
  "days": 7,
  "tool": "performance-test",
  "rows": []
}
```

### Monthly Summary
```json
{
  "source": "live",
  "days": 30,
  "tool": "performance-test",
  "rows": []
}
```

## Optimization Action Fixtures

### Hierarchy Analysis
```json
{
  "action": "hierarchy"
}
```

### Schedule Analysis
```json
{
  "action": "schedule"
}
```

### Evidence Analysis
```json
{
  "action": "evidence"
}
```

### Capacity Analysis
```json
{
  "action": "capacity"
}
```

## Integration Job Fixtures

### Sample Integration Request
```json
{
  "repository": "/tmp/test-repo",
  "mode": "analysis",
  "options": {
    "includeTests": true,
    "includeDocs": false
  }
}
```

## MCP Discovery Fixtures

### Sample MCP Server Request
```json
{
  "serverId": "test-server-001"
}
```
