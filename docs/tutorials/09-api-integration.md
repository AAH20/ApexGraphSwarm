# Tutorial 9: API Integration

## Overview

ApexGraphSwarm provides explicit integration adapters for external frameworks, models, and services. This tutorial covers the available adapters, configuration patterns, and how to build custom integrations.

## Available Adapters

### Configured HTTP/Service Adapters

| Adapter | Description |
|---------|-------------|
| Cognee | Knowledge graph service |
| MiroFish | Swarm optimization service |
| LangGraph | LangChain graph execution |
| CrewAI | Crew-based agent orchestration |
| Hermes | Hermes agent framework |

Each requires its documented service configuration. A successful submission can still require a later status check.

### Optional Local Harness Profiles

| Profile | Description |
|---------|-------------|
| OpenManus | Local agent harness |
| Understand Anything | Repository analysis plugin |

These depend on separately installed applications/plugins and reviewed profiles. Opening an existing Understand Anything viewer does not analyze a repository.

### Model Providers

| Provider | Description |
|----------|-------------|
| Codex | OpenAI Codex |
| Claude Code | Anthropic Claude Code |
| Cursor | Cursor AI editor |
| Google Antigravity | Google Antigravity |
| OpenCode | OpenCode CLI |
| Hermes | Hermes agent |

Availability in a selector is separate from a verified executable profile. Subscription access uses supported authenticated clients; it is not interchangeable with provider API billing.

### Inference Services

| Service | Description |
|---------|-------------|
| OpenRouter | Multi-provider inference API |
| vLLM | Local LLM serving |

Both require configured server-side credentials/endpoints and model IDs. vLLM selection does not provision a GPU.

## Configuration Pattern

### Environment Variables

All adapters use environment variables for configuration. See `apps/web/.env.example` for the full list.

```sh
# Example .env.local
INTEGRATION_ACCESS_TOKEN=your_workspace_token
OPENROUTER_API_KEY=your_openrouter_key
VLLM_BASE_URL=http://localhost:8000
VLLM_MODEL_ID=your-model-id
```

### Adapter Registration

Adapters are registered in `apps/web/lib/integration-catalog.ts`. Each adapter declares:
- **ID** — unique identifier
- **Name** — display name
- **Kind** — service type
- **Configuration schema** — required fields
- **Capabilities** — what operations it supports

### Execution Flow

1. **Design** — Configure the adapter in the workspace UI
2. **Validate** — Check configuration and connectivity
3. **Submit** — Send a bounded request to the adapter
4. **Poll** — Check status (for async operations)
5. **Reconcile** — Resolve uncertain outcomes

## Building a Custom Adapter

### Step 1: Define the Contract

Create a TypeScript interface in `apps/web/lib/`:

```typescript
export interface MyAdapterConfig {
  endpoint: string;
  apiKey: string;
  modelId: string;
}

export interface MyAdapterRequest {
  prompt: string;
  maxTokens: number;
  temperature?: number;
}

export interface MyAdapterResponse {
  text: string;
  usage: {
    promptTokens: number;
    completionTokens: number;
  };
  costMicrousd: number;
}
```

### Step 2: Implement the Adapter

```typescript
import { MyAdapterConfig, MyAdapterRequest, MyAdapterResponse } from './types';

export async function executeMyAdapter(
  config: MyAdapterConfig,
  request: MyAdapterRequest
): Promise<MyAdapterResponse> {
  const response = await fetch(`${config.endpoint}/v1/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${config.apiKey}`,
    },
    body: JSON.stringify({
      model: config.modelId,
      prompt: request.prompt,
      max_tokens: request.maxTokens,
      temperature: request.temperature ?? 0.7,
    }),
  });

  if (!response.ok) {
    throw new Error(`Adapter error: ${response.status}`);
  }

  const data = await response.json();
  return {
    text: data.choices[0].text,
    usage: {
      promptTokens: data.usage.prompt_tokens,
      completionTokens: data.usage.completion_tokens,
    },
    costMicrousd: calculateCost(data.usage),
  };
}
```

### Step 3: Register in the Catalog

Add your adapter to `integration-catalog.ts`:

```typescript
export const integrationCatalog = [
  // ... existing adapters
  {
    id: 'my-adapter',
    name: 'My Custom Adapter',
    kind: 'inference',
    configSchema: {
      endpoint: { type: 'string', required: true },
      apiKey: { type: 'string', required: true, secret: true },
      modelId: { type: 'string', required: true },
    },
    capabilities: ['complete', 'embed'],
    execute: executeMyAdapter,
  },
];
```

### Step 4: Add UI Configuration

Create a configuration component in `apps/web/components/`:

```tsx
export function MyAdapterConfig({ config, onChange }: {
  config: MyAdapterConfig;
  onChange: (config: MyAdapterConfig) => void;
}) {
  return (
    <div>
      <label>
        Endpoint
        <input
          type="text"
          value={config.endpoint}
          onChange={(e) => onChange({ ...config, endpoint: e.target.value })}
        />
      </label>
      <label>
        API Key
        <input
          type="password"
          value={config.apiKey}
          onChange={(e) => onChange({ ...config, apiKey: e.target.value })}
        />
      </label>
      <label>
        Model ID
        <input
          type="text"
          value={config.modelId}
          onChange={(e) => onChange({ ...config, modelId: e.target.value })}
        />
      </label>
    </div>
  );
}
```

## MCP Integration

### Discovery

MCP discovery supports the documented handshake/HTTP subset. Navigate to [http://127.0.0.1:3010/ecosystem](http://127.0.0.1:3010/ecosystem) to discover configured MCP servers.

### Binding Tools

1. Discover available tools from an MCP server
2. Select specific tools to bind to a specialist
3. The binding is exact — selecting a gateway does not grant all tools

### Limitations

- Not universal support for every MCP transport
- Not every protocol revision
- Not every gateway
- Not every authentication mode

## Skills Integration

### Skill Review

The Ecosystem workspace accepts skill manifests/content for provenance and metadata checks. It does not fetch, install, or execute arbitrary packages.

### Skill Binding

1. Review the skill content in the Ecosystem workspace
2. Record the skill ID, source URL, revision, and SHA-256
3. Bind the skill to a specialist in the team designer

> A recorded hash is not proof that content was fetched, verified, installed, or trusted.

## Durable Adapters

For production use, adapters should implement:

- **Idempotency** — Safe to retry without duplicate side effects
- **Bounded retries** — Limited retry attempts with backoff
- **Reconciliation** — Resolve uncertain outcomes
- **Quotas** — Respect rate limits and budgets
- **Isolated workers** — Separate processes or worktrees

See [durable adapter setup](../durable-adapters.md) for the full contract.

## Provider Receipts

OpenRouter usage receipts are normalized by the system. Provider invoice reconciliation is separate — you must reconcile actual invoices against recorded receipts.

## Decision Providers

### Laya

Laya uses its native HTTP decision API. Supply bounded context and typed choice, score, or yes/no questions. Results show probability distributions, a user-selected review threshold, measured request latency, and operator-configured cost estimates.

### AnyJev

AnyJev uses the optional ApexGraphSwarm bridge around its Python SDK and a separately operated vLLM server.

> No model weights are bundled or downloaded automatically. Unavailable providers remain visibly unconfigured.

## Integration Best Practices

1. **Start with fixture work** — Use `fixture` execution class for testing before connecting real services
2. **Configure budgets** — Set `budget_microusd` before creating runs with paid services
3. **Use idempotency keys** — Prevent duplicate charges on retries
4. **Monitor costs** — Track `spentMicrousd` against `budgetMicrousd`
5. **Reconcile promptly** — Resolve `needs_reconciliation` tasks as soon as possible
6. **Keep secrets server-side** — Never put credentials in browser code or Git
7. **Test with small inputs** — Verify adapter behavior before scaling up

## Next Steps

- [Tutorial 5: Governance](05-governance.md) — Design teams that use these adapters.
- [Tutorial 10: Custom Templates](10-custom-templates.md) — Build reusable templates for common patterns.
