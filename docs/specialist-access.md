# Local specialist access contracts

Specialist access contracts are an opt-in admission check at the local SQLite `ControlStore` boundary. They bind an operator-reviewed exported specialist design and one exact graph-review input to a single enrolled worker, principal, logical agent, node, action, audience, purpose, model, adapter, tool, resource, and expiry. They do not connect to Agent IAM/JIT IAM, verify MCP gateway identity, install or execute declared skills/tools, provide external ACL enforcement, or sandbox provider/harness work.

## Local operator flow

Use only the local control CLI for contract configuration and issuance. The web designer exports a request for the local operator; it cannot configure approvers, approve, activate, or revoke a contract. First enroll the target worker and approver workers with distinct principal IDs. Configure the local approver allowlist, then submit the exact design export and assignment to `createSpecialistContract`:

```json
{
  "action": "createSpecialistContract",
  "dbPath": "/path/to/control.sqlite",
  "idempotencyKey": "review-contract-2026-09-27-a",
  "design": {"schemaVersion": 1, "id": "design-1", "name": "Reviewed design", "agents": [], "teams": [], "nodes": []},
  "assignment": {
    "specialistId": "reviewer-1", "nodeId": "repo-main", "action": "read",
    "audience": "apexgraphswarm", "purpose": "dependency-review",
    "workerId": "worker-17", "principalId": "principal-reviewer",
    "logicalAgentId": "agent-reviewer", "modelId": "vendor/model-v1",
    "adapterId": "openrouter", "toolId": "integration:openrouter:review",
    "resourceId": "model:vendor/model-v1",
    "mcpBinding": {"serverId": "graph-tools", "toolName": "read-graph", "gatewayId": "local-gateway"},
    "expiresAt": 1800000000,
    "executionInput": {"goal": "Review this graph snapshot.", "graph": {}, "parameters": {"maxOutputTokens": 600}}
  }
}
```

The empty design arrays above are placeholders for the exported design; a real request must include a fully validated design with the referenced specialist, team assignment, and scope node.

The exact `executionInput` and full design are retained in the pending contract status response so local approvers can inspect the evidence before approving. The design limit is 512 KiB, execution input is limited to 1 MiB, and the combined stored review record is capped at 1.5 MiB. The CLI request/response envelope remains 2 MiB. No credential may appear in design, assignment, or execution input.

`configureSpecialistApprovers` accepts 1–64 exact principal IDs. `approveSpecialistContract` takes only a contract ID, enrolled worker ID, and worker credential. The principal is derived from the stored worker enrollment; caller-supplied principal IDs do not count. Only current allowlisted workers count, each principal counts once, and the target specialist principal cannot approve its own contract. Approval rows bind to the immutable contract digest. Changing the allowlist demotes active contracts to `pending_approval`; removed principals' approvals are deleted, and a local administrator must reactivate a contract after its live quorum is valid again.

`activateSpecialistContract` is a local administrator CLI operation and succeeds only while the contract is unexpired and its authenticated quorum is currently valid. `revokeSpecialistContract` denies future claims and heartbeats. `specialistContractStatus` exposes the stored evidence, hashes, recorded and currently valid approval counts, expiry, and lifecycle status. Exact retries of `createSpecialistContract` return the original record, even after expiry; reusing its idempotency key with different input fails.

## Bind a plan and dispatch

The local CLI action `bindSpecialistContract` takes `{contractId, plan, taskId}` where `taskId` is the plan task key. It verifies the active contract, current quorum, expiry, exact logical agent/model/adapter/tool/resource, review operation, and canonical execution-input hash. It returns a copied plan with that task's `specialistContractId` and generated `payload.specialistAccess` provenance. This does not create a run, grant a capability, enroll a worker, or dispatch work.

`create_run` checks the active contract again. Specialist-bound tasks must be nonfixture, use an exact external tool/resource, opt into configured resource capacity, and carry the exact binding and reviewed input. At claim, the worker must use authenticated credentials for the precise enrolled `workerId`/`principalId` in the contract. The ordinary exact access grant is still required independently; contracts never mint grants or credentials. Claims and heartbeats recheck worker status, contract state/expiry, and the current authenticated approval quorum. Leases are capped by the contract expiry.

The current contract implementation only supports `read`/`plan` review actions, delegation depth zero, OpenRouter/vLLM adapters, and the exact `integration:<adapter>:review` tool. Administrative and physical actuation actions fail closed. Model/adapter identifiers are operator-supplied exact bindings; the control plane does not probe whether a provider model or adapter is configured. Skill hashes and MCP binding hashes preserve provenance only; they do not prove an artifact is safe, a tool is installed, a gateway is trusted, or an operation was mediated by it. `nodeExternalRef` is recorded but never dereferenced or externally authorized.

The local administrator CLI is a trusted machine boundary, not an authenticated enterprise administrator identity. Revocation prevents new claims and lease renewal but cannot stop a call already underway. Unknown effects remain subject to the existing durable reconciliation flow. This is not production IAM or universal enforcement: provider, network, harness, or direct tool paths outside `ControlStore` may not be mediated by these contracts.
