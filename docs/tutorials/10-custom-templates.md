# Tutorial 10: Custom Templates

## Overview

ApexGraphSwarm's template system lets you create reusable patterns for common workflows. This tutorial covers the template schema, built-in templates, and how to build and share custom templates.

## What Are Templates?

Templates are pre-configured patterns for:
- **Specialist teams** — Reusable team structures with common skill/tool bindings
- **Scope hierarchies** — Pre-built scope trees for common architectures
- **Evaluation plans** — Versioned task splits with held-out gates
- **Delegation plans** — Compiled schedules with model/tool/resource mappings
- **Analytics dashboards** — Pre-configured visualizations and cohorts

## Template Schema

Templates use a validated JSON schema:

```json
{
  "version": 1,
  "id": "my-template",
  "name": "My Custom Template",
  "description": "A reusable pattern for...",
  "kind": "specialist-team",
  "data": {
    // Template-specific data
  },
  "metadata": {
    "author": "your-name",
    "createdAt": "2026-09-29T00:00:00Z",
    "tags": ["example", "starter"]
  }
}
```

### Validation Rules

- `version` must be 1
- `id` must be unique and URL-safe
- `kind` must be one of: `specialist-team`, `scope-hierarchy`, `evaluation-plan`, `delegation-plan`, `analytics-dashboard`
- `data` must conform to the schema for the specified `kind`
- Imports are capped at **512 KiB**
- Unknown fields are rejected
- Cycles and dangling references are rejected

## Built-in Templates

### Specialist Team Templates

The workspace includes starter templates for common specialist roles:

| Template | Specialists | Skills | Tools |
|----------|-------------|--------|-------|
| Code Reviewer | reviewer, critic | code-review, security-scan | github-pr, semgrep |
| Documentation Writer | writer, editor | docs-generation, api-docs | filesystem-read |
| Test Engineer | tester, coverage-analyzer | test-generation, coverage | pytest, jest |
| Performance Analyst | profiler, optimizer | profiling, benchmarking | perf-tools |

### Scope Hierarchy Templates

| Template | Node Types | Use Case |
|----------|-----------|----------|
| Monorepo | repository, module, package | Single-repo multi-package projects |
| Microservices | repository, service, module | Multi-repo service architecture |
| Data Center | data-center, rack, fleet, device | Infrastructure monitoring |
| IoT Fleet | fleet, device, command-center | IoT device management |

## Creating a Custom Template

### Step 1: Design the Base Configuration

Start by designing the configuration in the workspace UI:

1. **For specialist teams:** Use the team designer at `/teams`
2. **For scope hierarchies:** Use the scope topology tool
3. **For evaluation plans:** Use the evaluation lab at `/evaluations`
4. **For delegation plans:** Use the delegation planner at `/delegation`

### Step 2: Export the Configuration

Each designer has an export function:

```typescript
// Example: Export a specialist team
const template = {
  version: 1,
  id: 'my-team-template',
  name: 'My Team Template',
  description: 'A reusable team for code review workflows',
  kind: 'specialist-team',
  data: {
    specialists: [
      {
        id: 'reviewer',
        name: 'Reviewer',
        responsibility: 'Reviews code for correctness and style',
        modelRef: 'claude-code',
        skills: [
          {
            id: 'code-review',
            sourceUrl: 'https://example.com/skills/code-review',
            revision: 'v1.0.0',
            sha256: 'abc123...'
          }
        ],
        tools: [
          { server: 'github', tool: 'pull-request-review' }
        ],
        iam: {
          provider: 'agentiam',
          subject: 'reviewer@workspace',
          owner: 'team-lead',
          tenant: 'default',
          audience: ['code-review'],
          purpose: 'Review pull requests',
          actions: ['read:code', 'write:review'],
          resources: ['repo:my-repo'],
          ttl: 300,
          maxDelegationDepth: 1,
          approvalQuorum: 1
        }
      }
    ],
    teams: [
      {
        id: 'review-team',
        name: 'Review Team',
        members: ['reviewer']
      }
    ]
  },
  metadata: {
    author: 'your-name',
    createdAt: '2026-09-29T00:00:00Z',
    tags: ['review', 'starter']
  }
};
```

### Step 3: Validate the Template

Use the import function to validate:

1. Open the relevant designer
2. Choose **Import**
3. Select your template JSON
4. The system validates the schema and reports any errors

### Step 4: Save and Share

Save the template to browser storage or export it as a JSON file. Share the file with your team.

## Template Patterns

### Pattern 1: Environment-Specific Teams

Create separate templates for development, staging, and production:

```json
{
  "id": "reviewer-dev",
  "name": "Reviewer (Development)",
  "data": {
    "specialists": [{
      "id": "reviewer",
      "iam": {
        "tenant": "dev",
        "resources": ["repo:my-repo:dev"],
        "ttl": 300
      }
    }]
  }
}
```

```json
{
  "id": "reviewer-prod",
  "name": "Reviewer (Production)",
  "data": {
    "specialists": [{
      "id": "reviewer",
      "iam": {
        "tenant": "prod",
        "resources": ["repo:my-repo:prod"],
        "ttl": 60,
        "approvalQuorum": 2
      }
    }]
  }
}
```

### Pattern 2: Incremental Scope Assignment

Build scope hierarchies incrementally:

```json
{
  "id": "scope-incremental",
  "kind": "scope-hierarchy",
  "data": {
    "nodes": [
      { "id": "root", "type": "repository", "label": "My Repo" },
      { "id": "module-a", "type": "module", "label": "Module A", "parent": "root" },
      { "id": "module-b", "type": "module", "label": "Module B", "parent": "root" },
      { "id": "service-a1", "type": "service", "label": "Service A1", "parent": "module-a" }
    ]
  }
}
```

### Pattern 3: Evaluation Gates

Create evaluation plans with held-out gates:

```json
{
  "id": "eval-gate-v1",
  "kind": "evaluation-plan",
  "data": {
    "version": 1,
    "trainingSplit": 0.7,
    "heldOutSplit": 0.3,
    "gates": [
      {
        "id": "quality-gate",
        "metric": "task-quality",
        "threshold": 0.85
      },
      {
        "id": "budget-gate",
        "metric": "cost-per-result",
        "threshold": 500
      }
    ]
  }
}
```

## Using Templates

### Importing a Template

1. Open the relevant designer
2. Choose **Import**
3. Select the template JSON file
4. Review the imported configuration
5. Customize as needed
6. Save or export the customized version

### Applying a Template

1. Import the template
2. Review the configuration
3. For specialist teams: Assign to scope nodes
4. For scope hierarchies: Attach to a repository
5. For evaluation plans: Run the evaluation
6. For delegation plans: Compile and activate

## Template Best Practices

1. **Use descriptive IDs** — `reviewer-prod` is better than `template-1`
2. **Include metadata** — Author, date, and tags help with discovery
3. **Document assumptions** — Note any external dependencies or prerequisites
4. **Validate before sharing** — Always test the import
5. **Version your templates** — Include a version in the ID or metadata
6. **Keep secrets out** — Templates should reference secrets, not contain them
7. **Bound the scope** — Templates should be specific enough to be useful, general enough to be reusable

## Template Repository

To share templates with your team:

1. Create a `templates/` directory in your project
2. Store template JSON files with descriptive names
3. Document each template in a README
4. Version control the templates
5. Review and validate templates before merging

## Next Steps

- [Tutorial 5: Governance](05-governance.md) — Design specialist teams that use templates.
- [Tutorial 9: API Integration](09-api-integration.md) — Integrate templates with external services.
- [Tutorial 1: Getting Started](01-getting-started.md) — Return to the basics.
