"""
Agentic NP-Hard Kernel: The Mathematical Operating Engine for Apex Agentic AI.
Deterministically solving the 10 fundamental NP-Hard computational bottlenecks
across tool routing, DAG workflows, prefix caching, speculative rollouts,
self-healing DAGs, submodular memory, Pareto routing, deadlock-free locks,
least-privilege RBAC, and Byzantine multi-agent verification.
"""

from .core.models import (
    ToolDefinition, ToolRoutingResult, SubTask, WorkflowDAGResult,
    ContextPromptBlock, PrefixCacheResult, SpeculativeActionNode,
    SpeculativeTreeResult, TaskFailureEvent, SelfHealingDAGResult,
    AgentMemoryRecord, SubmodularMemoryResult, ModelOption,
    ParetoRoutingResult, AgentResourceRequest, ResourceScheduleResult,
    CapabilityRule, LeastPrivilegeResult, AgentExecutionReceipt,
    ByzantineConsensusResult
)
from .core.tool_routing import CombinatorialToolRouter
from .core.workflow_dag import WorkflowDAGSynthesizer
from .core.prefix_kv_cache import PrefixKVCacheOptimizer
from .core.speculative_tree import SpeculativeTreeSearchSolver
from .core.fault_tolerant_dag import SelfHealingDAGReconfigurator
from .core.submodular_memory import SubmodularMemoryRetriever
from .core.pareto_model_router import ParetoModelRouter
from .core.sandbox_resource_scheduler import SandboxResourceScheduler
from .core.least_privilege_rbac import LeastPrivilegeRBACSolver
from .core.byzantine_consensus import ByzantineAgentConsensus
from .engine import AgenticNPHardEngine

__all__ = [
    "ToolDefinition", "ToolRoutingResult", "SubTask", "WorkflowDAGResult",
    "ContextPromptBlock", "PrefixCacheResult", "SpeculativeActionNode",
    "SpeculativeTreeResult", "TaskFailureEvent", "SelfHealingDAGResult",
    "AgentMemoryRecord", "SubmodularMemoryResult", "ModelOption",
    "ParetoRoutingResult", "AgentResourceRequest", "ResourceScheduleResult",
    "CapabilityRule", "LeastPrivilegeResult", "AgentExecutionReceipt",
    "ByzantineConsensusResult",
    "CombinatorialToolRouter",
    "WorkflowDAGSynthesizer",
    "PrefixKVCacheOptimizer",
    "SpeculativeTreeSearchSolver",
    "SelfHealingDAGReconfigurator",
    "SubmodularMemoryRetriever",
    "ParetoModelRouter",
    "SandboxResourceScheduler",
    "LeastPrivilegeRBACSolver",
    "ByzantineAgentConsensus",
    "AgenticNPHardEngine",
]

__version__ = "1.0.0"
