# ApexGraphSwarm Monitoring

Prometheus + Grafana monitoring stack for ApexGraphSwarm.

## Quick Start

```bash
cd monitoring/
cp .env.example .env  # Edit as needed
docker-compose up -d
```

## Access

| Service | URL | Default Credentials |
|---------|-----|---------------------|
| Grafana | http://localhost:3000 | admin / admin |
| Prometheus | http://localhost:9090 | - |
| Alertmanager | http://localhost:9093 | - |
| Exporter Metrics | http://localhost:8000/metrics | - |

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APEXGRAPH_DB_HOST_PATH` | `./` | Host path to directory containing `control.db` |
| `GRAFANA_ADMIN_USER` | `admin` | Grafana admin username |
| `GRAFANA_ADMIN_PASSWORD` | `admin` | Grafana admin password |
| `APEXGRAPH_METRICS_PORT` | `8000` | Exporter HTTP port |
| `APEXGRAPH_SCRAPE_INTERVAL` | `15` | Scrape interval in seconds |

### Adding the Control DB

The exporter reads from a SQLite control store. Mount the directory containing
your `control.db` file:

```bash
# In .env
APEXGRAPH_DB_HOST_PATH=/path/to/your/apexgraphswarm/data
```

## Metrics Exported

| Metric | Type | Description |
|--------|------|-------------|
| `apexgraphswarm_attempts_total` | Counter | Total attempts by outcome |
| `apexgraphswarm_attempts_running` | Gauge | Currently running attempts |
| `apexgraphswarm_tasks_pending` | Gauge | Pending tasks |
| `apexgraphswarm_tasks_blocked` | Gauge | Blocked tasks |
| `apexgraphswarm_tasks_running` | Gauge | Running tasks |
| `apexgraphswarm_tasks_succeeded` | Gauge | Succeeded tasks |
| `apexgraphswarm_tasks_failed` | Gauge | Failed tasks |
| `apexgraphswarm_agents_active` | Gauge | Active workers |
| `apexgraphswarm_budget_microusd` | Gauge | Budget per run |
| `apexgraphswarm_spent_microusd` | Gauge | Spend per run |
| `apexgraphswarm_cost_microusd_total` | Counter | Total cost per run |
| `apexgraphswarm_resource_limit` | Gauge | Resource limit |
| `apexgraphswarm_resource_occupied` | Gauge | Resource occupied |
| `apexgraphswarm_attempt_duration_seconds` | Summary | Attempt duration |
| `apexgraphswarm_attempts_by_tool_total` | Counter | Attempts by tool |
| `apexgraphswarm_exporter_errors_total` | Counter | Exporter errors |

## Dashboards

- **Overview** (`overview.json`): Full operational view with latency, budget, resources
- **Summary** (`summary.json`): High-level KPIs and pie charts

## Alerting

Alert rules cover:
- Exporter availability
- High failure rates (warning at 30%, critical at 60%)
- High latency (P95 > 300s)
- Stalled attempts
- Budget exceeded / warning
- Resource exhaustion / starvation
- Task backlog / blocked tasks

## Stopping

```bash
docker-compose down
```

To remove all data:
```bash
docker-compose down -v
```
