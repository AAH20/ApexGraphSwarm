"""Red team framework for ApexGraphSwarm.

Automated attack generation, vulnerability discovery, exploit chaining,
and responsible disclosure. Zero-dependency Python 3.10+.
"""
from .red_team import RedTeamOrchestrator, RedTeamConfig, RedTeamResult, run_red_team
from .attack_surface import AttackSurface, SurfaceType, discover_all_surfaces
from .vulnerability import Vulnerability, Severity, discover_vulnerabilities
from .exploit_chain import ExploitChain, ChainStep, ChainStepStatus, build_exploit_chains
from .disclosure import (
    DisclosureReport,
    DisclosureStage,
    create_disclosure_report,
    generate_disclosure_summary,
    get_disclosure_recommendations,
)

__all__ = [
    "RedTeamOrchestrator",
    "RedTeamConfig",
    "RedTeamResult",
    "run_red_team",
    "AttackSurface",
    "SurfaceType",
    "discover_all_surfaces",
    "Vulnerability",
    "Severity",
    "discover_vulnerabilities",
    "ExploitChain",
    "ChainStep",
    "ChainStepStatus",
    "build_exploit_chains",
    "DisclosureReport",
    "DisclosureStage",
    "create_disclosure_report",
    "generate_disclosure_summary",
    "get_disclosure_recommendations",
]
