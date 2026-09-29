"""Example 23: Specialist access contracts.

Contracts bind specialist designs to exact task assignments
with approval quorums, TTL, and revocation.
"""
from apexgraphswarm.control import ControlStore

store = ControlStore(":memory:")

# Configure approvers
approvers = store.configure_specialist_approvers([
    "principal-1", "principal-2", "principal-3",
])
print(f"Configured {approvers['count']} approvers")
print(f"Changed: {approvers['changed']}")

# Create a specialist contract
design = {
    "schemaVersion": 1,
    "id": "design-1",
    "name": "Code Review Team",
    "agents": [
        {
            "id": "reviewer-1",
            "name": "Senior Reviewer",
            "role": "code-reviewer",
            "harnessId": "harness-local",
            "modelRef": "model:gpt-4",
            "policy": {
                "provider": "agentiam-lab",
                "subjectRef": "agent:reviewer-1",
                "ownerRef": "principal-1",
                "tenantRef": "tenant-1",
                "audience": "internal",
                "purpose": "code-review",
                "actions": ["read-code", "write-review"],
                "resourceIds": ["repo:src"],
                "ttlSeconds": 300,
                "maxDelegationDepth": 2,
                "approvalQuorum": 2,
            },
            "skills": [
                {
                    "id": "code-review",
                    "sourceUrl": "https://example.com/skills/code-review",
                    "revision": "v1.0.0",
                    "sha256": "a" * 64,
                }
            ],
            "tools": [
                {"serverId": "mcp-local", "toolName": "read_file", "gatewayId": "gw-1"}
            ],
        }
    ],
    "teams": [{"id": "team-1", "name": "Review Team", "agentIds": ["reviewer-1"]}],
    "nodes": [{"id": "repo:src", "label": "Source", "kind": "module"}],
}

assignment = {
    "specialistId": "reviewer-1",
    "nodeId": "repo:src",
    "action": "read-code",
    "audience": "internal",
    "purpose": "code-review",
    "workerId": "worker-1",
    "principalId": "principal-1",
    "logicalAgentId": "agent:reviewer-1",
    "modelId": "model:gpt-4",
    "adapterId": "adapter-local",
    "toolId": "integration:adapter-local:review",
    "resourceId": "repo:src",
    "mcpBinding": "mcp-local:read_file",
    "expiresAt": 9999999999.0,
    "executionInput": {"goal": "Review authentication code"},
}

contract = store.create_specialist_contract(
    idempotency_key="contract-1",
    design=design,
    assignment=assignment,
)
print(f"\nContract created: {contract['contractId']}")
print(f"Status: {contract['status']}")

# Approve the contract (requires worker authentication)
# In practice, each approver would authenticate
# store.approve_specialist_contract(contract_id, worker_id, credential)

# Check status
status = store.specialist_contract_status(contract["contractId"])
print(f"Contract status: {status['status']}")

store.close()
