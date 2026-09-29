"""Unified Engine Facade for Agentic AI NP-Hard Optimization."""
from typing import List, Dict, Tuple, Optional, Any
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
from .adapters.software_engineering import run_software_engineering_benchmark
from .adapters.cloud_sre_incident import run_cloud_sre_benchmark

class AgenticNPHardEngine:
    """
    Unified Engine solving the 10 Apex NP-Hard Computational Bottlenecks in Modern Agentic AI.
    Pure Python 3.10+ Standard Library with microsecond/sub-millisecond deterministic guarantees.
    """

    # 1. Combinatorial Tool Routing
    def route_tools(
        self,
        tool_inventory: List[ToolDefinition],
        max_latency_ms: float = 500.0,
        max_token_budget: int = 4000
    ) -> ToolRoutingResult:
        router = CombinatorialToolRouter(tool_inventory)
        return router.solve(max_latency_ms, max_token_budget)

    # 2. Workflow DAG Synthesis
    def synthesize_workflow_dag(self, tasks: List[SubTask]) -> WorkflowDAGResult:
        synthesizer = WorkflowDAGSynthesizer(tasks)
        return synthesizer.solve()

    # 3. Prefix-KV Cache Packing
    def optimize_prefix_cache(
        self,
        blocks: List[ContextPromptBlock],
        max_vram_tokens: int = 32768
    ) -> PrefixCacheResult:
        optimizer = PrefixKVCacheOptimizer(blocks, max_vram_tokens)
        return optimizer.solve()

    # 4. Speculative Tree Rollouts
    def search_speculative_rollouts(
        self,
        nodes: List[SpeculativeActionNode],
        token_budget: int = 10000
    ) -> SpeculativeTreeResult:
        solver = SpeculativeTreeSearchSolver(nodes, token_budget)
        return solver.solve()

    # 5. Fault-Tolerant Workflow Reconfiguration
    def reconfigure_workflow(
        self,
        initial_tasks: List[SubTask],
        failure_event: TaskFailureEvent,
        fallback_templates: Dict[str, SubTask]
    ) -> SelfHealingDAGResult:
        healer = SelfHealingDAGReconfigurator(initial_tasks)
        return healer.reconfigure(failure_event, fallback_templates)

    # 6. Submodular Memory Retrieval
    def retrieve_submodular_memory(
        self,
        memory_pool: List[AgentMemoryRecord],
        k_records: int = 5,
        diversity_penalty: float = 0.35
    ) -> SubmodularMemoryResult:
        retriever = SubmodularMemoryRetriever(memory_pool, diversity_penalty)
        return retriever.solve(k_records)

    # 7. Multi-Objective Model Routing
    def route_model_pareto(
        self,
        catalog: List[ModelOption],
        max_cost_budget: Optional[float] = None,
        max_latency_ms: Optional[float] = None,
        min_fidelity: Optional[float] = None
    ) -> ParetoRoutingResult:
        router = ParetoModelRouter(catalog)
        return router.solve(max_cost_budget, max_latency_ms, min_fidelity)

    # 8. Deadlock-Free Concurrency Allocation
    def schedule_sandbox_resources(
        self,
        requests: List[AgentResourceRequest]
    ) -> ResourceScheduleResult:
        scheduler = SandboxResourceScheduler(requests)
        return scheduler.solve()

    # 9. Least-Privilege Safety RBAC
    def solve_least_privilege_rbac(
        self,
        capabilities: List[CapabilityRule],
        required_actions: List[Tuple[str, str]]
    ) -> LeastPrivilegeResult:
        solver = LeastPrivilegeRBACSolver(capabilities)
        return solver.solve(required_actions)

    # 10. Byzantine Consensus
    def verify_byzantine_consensus(
        self,
        agent_nodes: List[str],
        receipts: List[AgentExecutionReceipt]
    ) -> ByzantineConsensusResult:
        bft = ByzantineAgentConsensus(agent_nodes)
        return bft.verify_and_agree(receipts)

    # Scenario Benchmarks
    def run_software_engineering_benchmark(self) -> Dict[str, Any]:
        return run_software_engineering_benchmark()

    def run_cloud_sre_benchmark(self) -> Dict[str, Any]:
        return run_cloud_sre_benchmark()
