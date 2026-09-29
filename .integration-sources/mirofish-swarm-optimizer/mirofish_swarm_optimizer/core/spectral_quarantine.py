"""
Spectral Graph Laplacian Sybil & Echo-Chamber Quarantine Solver.
Detects coordinated adversarial bots, sybil agents, and synthetic echo chambers
using Normalized Graph Laplacian Spectral Partitioning and Cheeger Sweep Cuts.
Replaces naive rule-based heuristics with provable conductance bounds.
"""
import time
import math
from typing import List, Dict, Tuple, Set
from .models import QuarantineResult

class SpectralSybilQuarantine:
    """
    Applies Spectral Graph Theory to isolate polarized echo chambers or sybil clusters.
    Uses Power Iteration with Deflation to compute the Fiedler vector (second smallest eigenvector of L).
    """

    def __init__(self, agents: List[str], adjacency_matrix: List[List[float]]):
        self.agents = agents
        self.n = len(agents)
        self.A = adjacency_matrix

    def solve(self, max_iterations: int = 100) -> QuarantineResult:
        t0 = time.perf_counter()
        n = self.n
        if n < 3:
            t1 = time.perf_counter()
            return QuarantineResult(
                quarantined_cluster=[],
                authentic_agents=self.agents,
                cheeger_conductance=0.0,
                spectral_fiedler_gap=0.0,
                algorithm="SPECTRAL_GRAPH_LAPLACIAN",
                execution_time_us=(t1 - t0) * 1e6
            )

        # Compute degree vector D
        degrees = [sum(self.A[i]) for i in range(n)]
        for i in range(n):
            if degrees[i] < 1e-6:
                degrees[i] = 1e-6  # Regularization for isolated nodes

        # Construct random walk transition matrix P = D^{-1} A
        # The stationary distribution is proportional to degree: pi_i = d_i / sum(d)
        sum_deg = sum(degrees)
        d_sqrt_inv = [1.0 / math.sqrt(d) for d in degrees]

        # Normalized Adjacency M = D^{-1/2} A D^{-1/2}
        # Trivial top eigenvector of M is v1 = D^{1/2} 1 / ||D^{1/2} 1||
        v1 = [math.sqrt(d) for d in degrees]
        norm_v1 = math.sqrt(sum(x * x for x in v1))
        v1 = [x / norm_v1 for x in v1]

        # Power iteration to find second largest eigenvector of M (which corresponds to Fiedler of L_sym)
        # Random initial vector orthogonalized against v1
        v2 = [math.sin(i * 1.6180339887) for i in range(n)]
        # Orthogonalize against v1
        dot_v1 = sum(v2[i] * v1[i] for i in range(n))
        v2 = [v2[i] - dot_v1 * v1[i] for i in range(n)]
        norm_v2 = math.sqrt(sum(x * x for x in v2))
        v2 = [x / max(norm_v2, 1e-9) for x in v2]

        # Power iteration: v <- M v, then re-orthogonalize against v1
        lambda_2 = 0.0
        for _ in range(max_iterations):
            # Matrix-vector multiplication w = M v2
            # First scale by D^{-1/2}
            scaled_v = [v2[j] * d_sqrt_inv[j] for j in range(n)]
            # Multiply by A
            Av = [sum(self.A[i][j] * scaled_v[j] for j in range(n)) for i in range(n)]
            # Scale by D^{-1/2}
            w = [Av[i] * d_sqrt_inv[i] for i in range(n)]

            # Orthogonalize against v1
            proj = sum(w[i] * v1[i] for i in range(n))
            w = [w[i] - proj * v1[i] for i in range(n)]

            norm_w = math.sqrt(sum(x * x for x in w))
            if norm_w < 1e-9:
                break
            v2 = [x / norm_w for x in w]
            lambda_2 = norm_w

        # Transform to normalized cut coordinate: y = D^{-1/2} v2
        y = [v2[i] * d_sqrt_inv[i] for i in range(n)]

        # Cheeger sweep cut: sort vertices by y_i
        sorted_indices = sorted(range(n), key=lambda idx: y[idx])

        # Sweep through cuts to find minimum conductance cut
        best_conductance = float('inf')
        best_split_idx = n // 2

        vol_total = sum(degrees)

        for cut_idx in range(1, n):
            set_s = set(sorted_indices[:cut_idx])
            vol_s = sum(degrees[i] for i in set_s)
            vol_s_c = vol_total - vol_s
            min_vol = min(vol_s, vol_s_c)
            if min_vol < 1e-6:
                continue

            # Cut weight = sum of edges between S and S^c
            cut_weight = sum(
                self.A[i][j]
                for i in set_s
                for j in range(n)
                if j not in set_s
            )

            conductance = cut_weight / min_vol
            if conductance < best_conductance:
                best_conductance = conductance
                best_split_idx = cut_idx

        # Smaller set is the candidate quarantined cluster
        set_a = [self.agents[i] for i in sorted_indices[:best_split_idx]]
        set_b = [self.agents[i] for i in sorted_indices[best_split_idx:]]

        if len(set_a) <= len(set_b):
            quarantine = set_a
            authentic = set_b
        else:
            quarantine = set_b
            authentic = set_a

        fiedler_gap = max(0.0, 1.0 - lambda_2)
        t1 = time.perf_counter()

        return QuarantineResult(
            quarantined_cluster=quarantine,
            authentic_agents=authentic,
            cheeger_conductance=best_conductance if best_conductance < float('inf') else 0.0,
            spectral_fiedler_gap=fiedler_gap,
            algorithm="SPECTRAL_GRAPH_LAPLACIAN",
            execution_time_us=(t1 - t0) * 1e6
        )
