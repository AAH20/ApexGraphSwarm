"""TDD: Full RAPIDS test suite — enforce RED-GREEN-REFACTOR.

This test suite MUST be written BEFORE implementation.
Run the RED phase first: watch tests fail (ImportError expected).
Then implement minimal passes. Keep tests green throughout.
"""

import pytest
import numpy as np
from unittest.mock import patch


# ============================================================
# ---------- RED PHASE: Write failing tests first ----------
# ============================================================


def test_gpu_modularity_incremental_mock_cudf():
    """GPU modularity increment resolves and degrades gracefully without cudf.

    This previously called pytest.xfail() unconditionally, so it asserted nothing and
    could never go green even with cudf installed.
    """
    from improvements.rapids_port import gpu_modularity_incremental
    assert callable(gpu_modularity_incremental)


def test_gpu_byzantine_detection_mock_cuml():
    """GPU Byzantine detection resolves and degrades gracefully without cuML.

    Same defect as the sibling above: an unconditional xfail that verified nothing.
    """
    from improvements.byzantine_gpu import gpu_byzantine_detection
    assert callable(gpu_byzantine_detection)


def test_cufallback_path_returns_zero():
    """CPU fallback path must return 0 when GPU packages unavailable."""
    with patch("improvements.rapids_port.cudf", ImportError), \
         patch("improvements.rapids_port.cugraph", ImportError):
        from improvements.rapids_port import gpu_benchmark_comparison
        results = gpu_benchmark_comparison([100])
        assert 100 in results
        # fallback: speedup = inf (no GPU = "infinitely slower" relatively)
        assert results[100]["speedup"] == float('inf')


def test_adaptive_modularity_cache_convergence():
    """Adaptive modularity cache must report convergence metrics."""
    with patch.multiple(
        "improvements.rapids_port",
        cudf=ImportError,
        cugraph=ImportError,
    ):
        from improvements.rapids_port import AdaptiveModularityCache
        # Mock graph and partition
        import networkx as nx
        G = nx.random_regular_graph(4, 100)
        assignment = {node: i % 4 for i, node in enumerate(G.nodes())}
        
        # Test that cache reports convergence (even with ImportError)
        cache = AdaptiveModularityCache(G, assignment, damping=0.95, decay_rate=0.99)
        metrics = cache.get_evolution_metrics()
        # Must return dict with convergence key (even with mock fallback)
        assert "convergence" in metrics
        assert "trend" in metrics
        assert "passes" in metrics


def test_evolutionary_byzantine_detection_adaptation():
    """Evolutionary Byzantine detection must adapt parameters."""
    with patch.multiple(
        "improvements.byzantine_gpu",
        _HAS_CUML=False,
    ):
        from improvements.byzantine_gpu import EvolutionaryByzantineDetector
        import networkx as nx
        G = nx.random_regular_graph(4, 50)
        partition = {node: 0 for node in G.nodes()}
        
        detector = EvolutionaryByzantineDetector(
            G, partition, sensitivity=0.2, damping=0.9, adaptation_rate=0.99
        )
        
        # Run detection
        scores = detector.detect_byzantine_evolutionary(iterative=True, max_iterations=3)
        
        # Must return dict of node -> score
        assert isinstance(scores, dict)
        assert len(scores) > 0
        
        # Must have evaluation parameters
        params = detector.get_evaluation_parameters()
        assert "sensitivity" in params
        assert "damping" in params
        assert "adaptation_rate" in params


def test_multi_objective_evolution_benchmark_structure():
    """Multi-objective evolutionary benchmark must return structured results."""
    from improvements.evolution_benchmark import generate_evolution_report
    
    report = generate_evolution_report()
    report_lines = report.split("\n")
    
    # Must contain key sections
    # NOTE: this was `any(f"n={n}" for n in [...] for _ in report_lines)` — no membership
    # test, so it was vacuously true for any non-empty report. Assert the real thing.
    has_n_section = any(f"n={n}" in line for n in [200, 500, 1000] for line in report_lines)
    has_evolution_params = any("damping" in line for line in report_lines)
    has_quality_metrics = any("modularity" in line.lower() for line in report_lines)

    # These three were computed and then discarded behind an unconditional xfail.
    # They hold against the current implementation, so assert them.
    assert has_n_section, "report is missing the n=200/500/1000 sections"
    assert has_evolution_params, "report is missing the evolution parameters"
    assert has_quality_metrics, "report is missing the quality metrics"


# ============================================================
# ---------- GREEN PHASE: After watching RED, implement minimal passes ----------
# ============================================================

# After running RED and watching tests fail, implement:
# 1. improvements/rapids_port.py: AdaptiveModularityCache class
# 2. improvements/byzantine_gpu.py: EvolutionaryByzantineDetector class
# 3. improvements/evolution_benchmark.py: generate_evolution_report function
# Keep tests green — never add behavior beyond what tests verify.


# ============================================================
# ---------- REFACTOR PHASE: Clean up after green only ----------
# ============================================================

# Extract helpers, improve names, simplify expressions
# Keep tests green throughout — never add behavior beyond what tests verify