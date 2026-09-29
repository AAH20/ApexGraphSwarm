"""Attack surface discovery for ApexGraphSwarm.

Enumerates and categorizes the system's attack surface: control-plane
APIs, data stores, worker authentication, access grants, budget/lease
enforcement, and specialist contracts.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


class SurfaceType(enum.Enum):
    CONTROL_API = "control_api"
    IDENTITY = "identity"
    ACCESS_GRANT = "access_grant"
    BUDGET = "budget"
    LEASE = "lease"
    SPECIALIST_CONTRACT = "specialist_contract"
    CHECKPOINT = "checkpoint"
    LEDGER = "ledger"
    RECONCILIATION = "reconciliation"
    EXECUTION_GRAPH = "execution_graph"


@dataclass
class AttackSurface:
    """A discovered attack surface entry."""

    name: str
    surface_type: SurfaceType
    description: str
    attack_vectors: list[str] = field(default_factory=list)
    mitigations: list[str] = field(default_factory=list)
    severity_hint: str = "medium"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "surfaceType": self.surface_type.value,
            "description": self.description,
            "attackVectors": list(self.attack_vectors),
            "mitigations": list(self.mitigations),
            "severityHint": self.severity_hint,
        }


def discover_control_api_surface() -> list[AttackSurface]:
    """Enumerate control-plane API attack surfaces."""
    return [
        AttackSurface(
            name="create_run",
            surface_type=SurfaceType.CONTROL_API,
            description="Creates a DAG run with task reservations and budget.",
            attack_vectors=[
                "Submit oversized plan to exhaust MAX_PLAN_BYTES",
                "Cycle dependencies to bypass _validate_acyclic",
                "Set reservedCostMicrousd=0 on external tasks to skip authorization",
                "Submit duplicate idempotency_key with different plan",
            ],
            mitigations=[
                "Plan size capped at 2 MiB",
                "Dependency cycle detection",
                "External tasks require exact tool/resource scope",
                "Idempotency key returns prior run on conflict",
            ],
            severity_hint="medium",
        ),
        AttackSurface(
            name="claim",
            surface_type=SurfaceType.CONTROL_API,
            description="Atomically leases one ready task for a worker.",
            attack_vectors=[
                "Exhaust max_active slots to starve legitimate workers",
                "Claim with forged lease_token to hijack task",
                "Claim specialist-bound task without authenticated identity",
                "Bypass requireResourceCapacity check",
            ],
            mitigations=[
                "max_active global cap",
                "Lease token fencing via secrets.token_urlsafe",
                "Specialist contracts require authenticated dispatch",
                "Resource capacity check before claim",
            ],
            severity_hint="high",
        ),
        AttackSurface(
            name="heartbeat",
            surface_type=SurfaceType.CONTROL_API,
            description="Renews a worker's lease on a task.",
            attack_vectors=[
                "Extend lease beyond MAX_LEASE_SECONDS via integer overflow",
                "Heartbeat with revoked grant to probe state",
                "Heartbeat with mismatched worker_id to trigger race",
            ],
            mitigations=[
                "Lease duration bounded 1-300 seconds",
                "Grant revocation rechecked at heartbeat",
                "Worker identity verified via token digest",
            ],
            severity_hint="low",
        ),
        AttackSurface(
            name="complete",
            surface_type=SurfaceType.CONTROL_API,
            description="Settles a task with actual cost and result.",
            attack_vectors=[
                "Submit result larger than MAX_RESULT_BYTES",
                "Set actual_cost_microusd above reservedCostMicrousd",
                "Include credential fields in result to leak secrets",
                "Replay completion with same lease_token after fencing",
            ],
            mitigations=[
                "Result size capped at 1 MiB",
                "Budget breach flags run as exceeded",
                "Secret field rejection in payload/result",
                "Lease token cleared after completion",
            ],
            severity_hint="medium",
        ),
        AttackSurface(
            name="fail",
            surface_type=SurfaceType.CONTROL_API,
            description="Marks a task as failed, optionally retryable.",
            attack_vectors=[
                "Set retryable=True on external class to auto-retry",
                "Set actual_cost_microusd=0 to get free retries",
                "Fail all tasks to cascade descendant failures",
            ],
            mitigations=[
                "Auto-retry restricted to explicit idempotent classes",
                "Cost must be known and non-negative",
                "Max attempts enforced per task",
            ],
            severity_hint="low",
        ),
    ]


def discover_identity_surface() -> list[AttackSurface]:
    """Enumerate identity and authentication attack surfaces."""
    return [
        AttackSurface(
            name="worker_enrollment",
            surface_type=SurfaceType.IDENTITY,
            description="Enrolls a worker with a principal and expiry.",
            attack_vectors=[
                "Enroll with far-future expires_at to persist access",
                "Enroll duplicate worker_id to trigger ConflictError",
                "Enroll with empty token to probe error handling",
            ],
            mitigations=[
                "Duplicate worker_id rejected with ConflictError",
                "Expiry must be in the future",
                "Credential minted with secrets.token_urlsafe(32)",
            ],
            severity_hint="medium",
        ),
        AttackSurface(
            name="credential_verification",
            surface_type=SurfaceType.IDENTITY,
            description="Verifies worker credentials via constant-time hash comparison.",
            attack_vectors=[
                "Submit short credential to bypass length check",
                "Submit non-string credential to trigger TypeError",
                "Timing attack on hash comparison (mitigated by hmac.compare_digest)",
            ],
            mitigations=[
                "Length check 32-512 characters",
                "Constant-time comparison via hmac.compare_digest",
                "Same-length digest comparison on absent identity",
            ],
            severity_hint="low",
        ),
        AttackSurface(
            name="worker_revocation",
            surface_type=SurfaceType.IDENTITY,
            description="Revokes a worker's enrollment.",
            attack_vectors=[
                "Revoke with unknown worker_id to probe response",
                "Race revoke between heartbeat and revocation",
            ],
            mitigations=[
                "Revocation is idempotent (returns False if already revoked)",
                "Heartbeat rechecks revocation at each call",
            ],
            severity_hint="low",
        ),
    ]


def discover_access_surface() -> list[AttackSurface]:
    """Enumerate access grant attack surfaces."""
    return [
        AttackSurface(
            name="access_grant_creation",
            surface_type=SurfaceType.ACCESS_GRANT,
            description="Creates an exact capability grant for a principal/tool/resource.",
            attack_vectors=[
                "Grant max_budget_microusd=0 to create unusable grant",
                "Grant with far-future expiry to persist access",
                "Grant access to resource that task doesn't require",
            ],
            mitigations=[
                "Exact tuple matching at authorize time",
                "Grant expiry checked at claim",
                "Budget must be non-negative integer",
            ],
            severity_hint="medium",
        ),
        AttackSurface(
            name="access_authorization",
            surface_type=SurfaceType.ACCESS_GRANT,
            description="Authorizes exact principal/tool/resource tuple against grants.",
            attack_vectors=[
                "Submit principal_id=None to probe fail-closed behavior",
                "Submit negative budget to underflow",
                "Reuse exhausted grant budget across multiple claims",
            ],
            mitigations=[
                "Missing principal_id raises AccessDenied",
                "Budget must be known integer",
                "Cumulative spend tracked against max_budget_microusd",
            ],
            severity_hint="high",
        ),
    ]


def discover_budget_surface() -> list[AttackSurface]:
    """Enumerate budget and cost accounting attack surfaces."""
    return [
        AttackSurface(
            name="budget_exceeded",
            surface_type=SurfaceType.BUDGET,
            description="Detects when actual cost exceeds reservations or run budget.",
            attack_vectors=[
                "Submit actual_cost above reservedCostMicrousd to trigger breach",
                "Exploit integer overflow in micro-USD accumulation",
                "Set budget_microusd=0 to reject all paid tasks",
            ],
            mitigations=[
                "Breach flags run budget_exceeded",
                "Micro-USD bounded to 2^63-1",
                "Zero budget rejects paid tasks",
            ],
            severity_hint="medium",
        ),
        AttackSurface(
            name="unknown_cost_handling",
            surface_type=SurfaceType.BUDGET,
            description="Handles tasks where actual cost is unknown at completion.",
            attack_vectors=[
                "Submit unknown cost to leave reservation held indefinitely",
                "Probe needs_reconciliation state transitions",
            ],
            mitigations=[
                "Unknown cost marks task needs_reconciliation",
                "Reservation held until operator reconciles",
                "Receipt evidence required for settlement",
            ],
            severity_hint="low",
        ),
    ]


def discover_lease_surface() -> list[AttackSurface]:
    """Enumerate lease and concurrency attack surfaces."""
    return [
        AttackSurface(
            name="lease_expiry_recovery",
            surface_type=SurfaceType.LEASE,
            description="Recovers expired leases and requeues or fails tasks.",
            attack_vectors=[
                "Trigger recovery with future timestamp to requeue tasks prematurely",
                "Exploit ambiguous state to avoid failure cascade",
            ],
            mitigations=[
                "Recovery only processes tasks with lease_expires_at <= now",
                "Ambiguous tasks marked needs_reconciliation",
                "Fixture tasks safely requeued",
            ],
            severity_hint="low",
        ),
        AttackSurface(
            name="resource_capacity",
            surface_type=SurfaceType.LEASE,
            description="Enforces per-resource concurrency limits.",
            attack_vectors=[
                "Configure max_concurrency=0 to deadlock all tasks",
                "Submit tasks with resourceConcurrencyLimit=1 to serialize",
            ],
            mitigations=[
                "max_concurrency bounded 1-10000",
                "Per-run and global limits enforced",
            ],
            severity_hint="low",
        ),
    ]


def discover_specialist_surface() -> list[AttackSurface]:
    """Enumerate specialist contract attack surfaces."""
    return [
        AttackSurface(
            name="specialist_contract_creation",
            surface_type=SurfaceType.SPECIALIST_CONTRACT,
            description="Creates a specialist access contract with design and assignment.",
            attack_vectors=[
                "Submit design with 301 agents to exceed bound",
                "Submit skill.sourceUrl with credentials to exfiltrate",
                "Submit unsafe JSON keys (__proto__, constructor)",
            ],
            mitigations=[
                "Agent count bounded 1-300",
                "Skill URL must be HTTPS without credentials",
                "Unsafe JSON keys rejected",
            ],
            severity_hint="medium",
        ),
        AttackSurface(
            name="specialist_contract_approval",
            surface_type=SurfaceType.SPECIALIST_CONTRACT,
            description="Approves a specialist contract by a configured approver.",
            attack_vectors=[
                "Approve with non-approver principal to bypass quorum",
                "Approve revoked contract to reactivate",
            ],
            mitigations=[
                "Approver allowlist enforced",
                "Revoked contracts cannot be reactivated",
            ],
            severity_hint="high",
        ),
    ]


def discover_checkpoint_surface() -> list[AttackSurface]:
    """Enumerate checkpoint attack surfaces."""
    return [
        AttackSurface(
            name="checkpoint_submission",
            surface_type=SurfaceType.CHECKPOINT,
            description="Persists bounded per-attempt generated output.",
            attack_vectors=[
                "Submit checkpoint larger than MAX_CHECKPOINT_BYTES",
                "Submit credential fields in checkpoint value",
                "Exceed MAX_CHECKPOINTS_PER_ATTEMPT limit",
            ],
            mitigations=[
                "Checkpoint size capped at 64 KiB",
                "Secret field rejection",
                "Count and byte limits enforced per attempt",
            ],
            severity_hint="low",
        ),
    ]


def discover_reconciliation_surface() -> list[AttackSurface]:
    """Enumerate receipt reconciliation attack surfaces."""
    return [
        AttackSurface(
            name="provider_receipt_reconciliation",
            surface_type=SurfaceType.RECONCILIATION,
            description="Settles unknown-cost attempts from normalized provider receipts.",
            attack_vectors=[
                "Submit receipt with mismatched generationId to spoof cost",
                "Submit receipt with costUsd=0 to get free execution",
                "Submit duplicate receipts for same call",
            ],
            mitigations=[
                "Generation ID must match saved checkpoint",
                "Cost must reconcile to exact USD decimal",
                "Duplicate call receipts rejected",
            ],
            severity_hint="high",
        ),
    ]


def discover_all_surfaces() -> list[AttackSurface]:
    """Discover all attack surfaces."""
    surfaces: list[AttackSurface] = []
    surfaces.extend(discover_control_api_surface())
    surfaces.extend(discover_identity_surface())
    surfaces.extend(discover_access_surface())
    surfaces.extend(discover_budget_surface())
    surfaces.extend(discover_lease_surface())
    surfaces.extend(discover_specialist_surface())
    surfaces.extend(discover_checkpoint_surface())
    surfaces.extend(discover_reconciliation_surface())
    return surfaces
