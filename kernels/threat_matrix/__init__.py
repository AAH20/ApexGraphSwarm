"""Adversary emulation threat matrix for ApexGraphSwarm.

Zero-dependency Python 3.10+ implementation covering 11 tactic domains.
"""
from .matrix import TacticDomain, ThreatMatrix, Technique, Severity, build_default_matrix
from .emulator import EmulationResult, EmulationReport, EmulationStatus, AdversaryEmulator
from .detection import DetectionRule, Mitigation

__all__ = [
    "TacticDomain",
    "ThreatMatrix",
    "Technique",
    "Severity",
    "build_default_matrix",
    "EmulationResult",
    "EmulationReport",
    "EmulationStatus",
    "AdversaryEmulator",
    "DetectionRule",
    "Mitigation",
]
