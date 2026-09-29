"""Agentic Graph Swarm Kernel: Solvers for the 10 Apex NP-Hard Problems in Agentic Graph Engineering & Swarm Orchestration."""
from .engine import AgenticGraphSwarmEngine
from .adapters.digital_world_simulator import DigitalWorldSimulatorAdapter
from .adapters.enterprise_agentic_mesh import EnterpriseAgenticMeshAdapter

__version__ = "1.0.0"
__all__ = [
    "AgenticGraphSwarmEngine",
    "DigitalWorldSimulatorAdapter",
    "EnterpriseAgenticMeshAdapter",
]
