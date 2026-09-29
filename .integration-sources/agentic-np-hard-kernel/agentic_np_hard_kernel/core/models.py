"""Data contracts and model definitions for the 10 Apex NP-Hard Problems in Agentic AI."""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Set, Tuple, Optional, Any

# --- Problem 1: Combinatorial Tool Routing ---
@dataclass
class ToolDefinition:
    tool_id: str
    name: str
    expected_utility: float  # Expected task success probability / value contribution [0, 1]
    latency_ms: float
    token_cost: int
    required_prerequisites: List[str] = field(default_factory=list)  # Prerequisites tool IDs

@dataclass
class ToolRoutingResult:
    selected_tools: List[ToolDefinition]
    total_utility: float
    total_latency_ms: float
    total_token_cost: int
    algorithm: str
    execution_time_us: float

# --- Problem 2: Hierarchical Goal & Workflow DAG Synthesis ---
@dataclass
class SubTask:
    task_id: str
    name: str
    duration_ms: float
    dependencies: List[str]  # Must complete before this task can start
    assigned_role: str

@dataclass
class WorkflowDAGResult:
    task_schedule: Dict[str, float]  # task_id -> start_time_ms
    critical_path: List[str]
    total_makespan_ms: float
    parallelism_factor: float
    algorithm: str
    execution_time_us: float

# --- Problem 3: Shared Prefix-KV Cache & Memory Packing ---
@dataclass
class ContextPromptBlock:
    block_id: str
    prefix_tokens: List[int]
    total_tokens: int
    priority_weight: float
    associated_agent_id: str

@dataclass
class PrefixCacheResult:
    packed_execution_order: List[str]
    cache_hit_ratio: float
    saved_prefill_tokens: int
    vram_peak_tokens: int
    algorithm: str
    execution_time_us: float

# --- Problem 4: Speculative Multi-Branch Rollout Tree Search ---
@dataclass
class SpeculativeActionNode:
    node_id: str
    parent_id: Optional[str]
    action_description: str
    cumulative_cost: int
    verification_score: float  # [0, 1]
    is_terminal: bool
    depth: int

@dataclass
class SpeculativeTreeResult:
    optimal_path: List[str]
    total_tokens_spent: int
    highest_verification_score: float
    nodes_pruned: int
    algorithm: str
    execution_time_us: float

# --- Problem 5: Dynamic Fault-Tolerant Workflow Reconfiguration ---
@dataclass
class TaskFailureEvent:
    failed_task_id: str
    error_code: str
    fallback_candidates: List[str]

@dataclass
class SelfHealingDAGResult:
    repaired_schedule: Dict[str, float]
    makespan_increase_ms: float
    tasks_rerouted: int
    stability_score: float  # [0, 1]
    algorithm: str
    execution_time_us: float

# --- Problem 6: Submodular Multi-Agent Episodic Memory Retrieval ---
@dataclass
class AgentMemoryRecord:
    memory_id: str
    topic_tag: str
    content: str
    salience: float
    timestamp: float
    embedding: List[float]

@dataclass
class SubmodularMemoryResult:
    retrieved_records: List[AgentMemoryRecord]
    coverage_score: float
    semantic_diversity: float
    compression_ratio_pct: float
    algorithm: str
    execution_time_us: float

# --- Problem 7: Multi-Objective Model Routing ---
@dataclass
class ModelOption:
    model_id: str
    name: str
    cost_per_k_tokens: float
    latency_per_step_ms: float
    benchmark_fidelity: float  # Accuracy [0, 1]

@dataclass
class ParetoRoutingResult:
    selected_model: ModelOption
    is_pareto_optimal: bool
    hypervolume_delta: float
    algorithm: str
    execution_time_us: float

# --- Problem 8: Deadlock-Free Concurrency & Sandbox Allocation ---
@dataclass
class AgentResourceRequest:
    agent_id: str
    task_id: str
    required_exclusive_locks: List[str]  # E.g., ["git_worktree_1", "port_8080", "browser_ctx_A"]
    hold_duration_ms: float

@dataclass
class ResourceScheduleResult:
    execution_sequence: List[str]  # task_ids in deadlock-free sequence
    max_concurrent_workers: int
    total_wait_time_ms: float
    zero_deadlock_certified: bool
    algorithm: str
    execution_time_us: float

# --- Problem 9: Least-Privilege Dynamic Capability / Safety RBAC ---
@dataclass
class CapabilityRule:
    capability_id: str
    action_type: str  # E.g., "EXECUTE_SHELL", "WRITE_FILE", "NETWORK_EGRESS", "SIGN_TRANSACTION"
    resource_scope: str
    risk_weight: float

@dataclass
class LeastPrivilegeResult:
    granted_capabilities: List[CapabilityRule]
    total_risk_score: float
    blast_radius_reduction_pct: float
    algorithm: str
    execution_time_us: float

# --- Problem 10: Byzantine Agent Verification & Equivocation Consensus ---
@dataclass
class AgentExecutionReceipt:
    agent_id: str
    task_id: str
    merkle_state_root: str
    action_hash: str
    signature: str

@dataclass
class ByzantineConsensusResult:
    consensus_state_root: str
    quarantine_traitors: List[str]
    bft_agreement_reached: bool
    merkle_validity_certified: bool
    algorithm: str
    execution_time_us: float
