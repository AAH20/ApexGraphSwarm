# Tutorial 8: Deployment

## Overview

ApexGraphSwarm is designed as a **local, single-workspace deployment bound to loopback**. This tutorial covers deployment modes, production considerations, and the roadmap for hosted operation.

## Deployment Modes

### Local Development

```sh
npm --prefix apps/web ci
npm --prefix apps/web run dev
```

Open [http://127.0.0.1:3010](http://127.0.0.1:3010). This is the primary development mode.

### Local Production Build

```sh
npm --prefix apps/web run build
npm --prefix apps/web run start
```

The build prepares the project graph assets. Production mode uses the same port **3010**.

### What "Local-First" Means

- The Python control plane uses only the standard library
- The web application is a Next.js frontend backed by SQLite
- No cloud service is required for core functionality
- All data stays on your machine
- The deployment is bound to loopback (127.0.0.1)

## Production Considerations

### What the Current Deployment Provides

| Component | Status |
|-----------|--------|
| Durable local control plane | SQLite WAL, process restart survival |
| Graph analysis | Local Python analyzer, bounded imports |
| Specialist design | Browser-based, validated import/export |
| Swarm orchestration | Deterministic fixtures, bounded execution |
| Analytics | Stdlib engine, capped scans |
| Optimization lab | Bounded local experiments |

### What It Does NOT Provide

| Missing Component | Impact |
|-------------------|--------|
| Multi-tenant isolation | Single-user only |
| Distributed worker fleet | Local execution only |
| Secret broker | Manual secret management |
| Event streaming | Poll-based recovery only |
| Automated remote-job poller | Manual reconciliation |
| Provider budget estimator | Manual cost planning |
| Worktree manager | No automatic worktree isolation |
| Sandbox | No OS-level isolation |
| CPU/memory/network enforcement | No resource limits on workers |
| Hosted deployment | No one-click Vercel/Cloudflare/Supabase |

## Pre-Production Checklist

### 1. Database Backup and Restore

```sh
# Backup
cp .apexgraphswarm/control.sqlite3 .apexgraphswarm/control.sqlite3.backup

# Test restore
cp .apexgraphswarm/control.sqlite3.backup /tmp/test-restore.sqlite3
python3 -m apexgraphswarm.control <<'EOF'
{"action":"status","dbPath":"/tmp/test-restore.sqlite3"}
EOF
```

### 2. Worker Configuration

Ensure all worker processes use the same:
- `max_active` (default 4)
- `max_registered_agents` (default 300)

### 3. Secret Management

- Keep `INTEGRATION_ACCESS_TOKEN` in `apps/web/.env.local`
- Keep provider credentials server-side
- Never commit secrets to Git
- Review `apps/web/.env.example` for all required variables

### 4. Database Location

- Keep the SQLite database outside public/static web directories
- Keep it out of Git
- Do not place it on an unreliable shared/network filesystem

### 5. Test the Full Stack

```sh
python3 -m unittest discover tests
npm --prefix apps/web test
npm --prefix apps/web run typecheck
npm --prefix apps/web run build
```

## Deployment Roadmap

The incremental production work includes:

### Phase 1: Production Specialist Identity
- Extend local enforced review contracts with externally verified tenant identity
- JIT credentials, resource ACLs, auditable adapter receipts

### Phase 2: Durable Adapter Integration
- Unify task lifecycle and remote job status
- Idempotency, bounded retries, reconciliation, quotas
- Isolated workers/worktrees

### Phase 3: Graph Scale and Fidelity
- Incremental ingestion
- Compiler-backed language semantics
- Measured layout budgets
- Storage-backed graph queries

### Phase 4: Evidence-Driven Delegation
- Live model evaluations on held-out workloads
- Provider usage capture, rate provenance
- Invoice reconciliation

### Phase 5: Private Infrastructure Adapters
- Start with inventory and telemetry
- Add explicitly authorized command capabilities
- Independent safety controls

### Phase 6: Hosted Operation
- Select durable storage/queues
- Secrets management, tenant isolation
- Recovery, observability, budget admission
- Before exposing execution endpoints

## Hosting the Frontend Alone

> A hosted frontend alone **cannot** safely replace a durable local database, a long-running runner, or private infrastructure connectivity.

If you host the frontend (e.g., on Vercel), you lose:
- The SQLite control plane (needs local filesystem)
- The Python analyzer (needs local execution)
- The optimization kernels (need local compute)

The hosted frontend would be a read-only view at best.

## Network Binding

The default binding is loopback (127.0.0.1). To bind to a different interface:

```sh
# Next.js dev server
npm --prefix apps/web run dev -- -H 0.0.0.0 -p 3010

# Next.js production server
npm --prefix apps/web run start -- -H 0.0.0.0 -p 3010
```

> **Warning:** Binding to 0.0.0.0 exposes the workspace to the network. The control plane has no authentication layer. Only do this in a trusted network or behind a reverse proxy with authentication.

## Reverse Proxy Setup (Example: Nginx)

```nginx
server {
    listen 443 ssl;
    server_name apexgraphswarm.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:3010;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Docker Deployment (Basic)

```dockerfile
FROM node:20-alpine AS web
WORKDIR /app
COPY apps/web/package*.json ./apps/web/
RUN npm --prefix apps/web ci
COPY apps/web ./apps/web
RUN npm --prefix apps/web run build

FROM python:3.11-slim AS runtime
WORKDIR /app
COPY --from=web /app/apps/web/.next ./apps/web/.next
COPY --from=web /app/apps/web/public ./apps/web/public
COPY --from=web /app/apps/web/package.json ./apps/web/package.json
COPY apexgraphswarm ./apexgraphswarm
COPY integrations ./integrations
COPY scripts ./scripts

EXPOSE 3010
CMD ["npm", "--prefix", "apps/web", "run", "start"]
```

> This is a basic example. Production Docker deployment would need volume mounts for the SQLite database, secret management, and proper signal handling.

## Monitoring

### Health Check

```sh
curl -s http://127.0.0.1:3010/api/health
```

### Database Size

```sh
ls -la .apexgraphswarm/control.sqlite3
```

### Event Log

```sh
sqlite3 .apexgraphswarm/control.sqlite3 "SELECT * FROM events ORDER BY sequence DESC LIMIT 20;"
```

## Next Steps

- [Tutorial 6: Security](06-security.md) — Secure your deployment.
- [Tutorial 9: API Integration](09-api-integration.md) — Integrate with external services.
