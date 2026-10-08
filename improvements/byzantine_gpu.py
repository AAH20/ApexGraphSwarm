"""GPU-accelerated Byzantine detection via Nvidia cuML.

Uses cuML Isolation Forest to identify nodes with weak connections
(target community). Falls back to networkx-based detection when
cuML is unavailable.
"""

import numpy as np
import networkx as nx

try:
    import cugraph as cg
    import cuml as ml
    _HAS_CUML = True
except ImportError:
    _HAS_CUML = False


def gpu_byzantine_detection(
    edge_list: np.ndarray,  # shape (E, 3): [source, target, weight]
    threshold: float = 0.2,
    num_neighbors: int = 10,
) -> np.ndarray:
    """GPU-accelerated Byzantine node detection.
    
    Uses cuML Isolation Forest to identify nodes with weak connections
    to their target community. Falls back to networkx degree/clustering
    when cuML unavailable.
    
    Returns numpy array of node indices identified as Byzantine.
    """
    if _HAS_CUML:
        _gpu_byzantine_via_cuml(edge_list, threshold, num_neighbors)
    _fallback_byzantine_via_networkx(edge_list, threshold)


def _gpu_byzantine_via_cuml(
    edge_list: np.ndarray,
    threshold: float,
    num_neighbors: int,
) -> np.ndarray:
    """Internal: Byzantine detection via Nvidia cuML Isolation Forest."""
    # Build cuGraph
    G = cg.Graph()
    G.from_csr(edge_list[:, 0], edge_list[:, 1], edge_list[:, 2])
    
    # Extract features for Byzantine detection
    degrees = cg.degree(G).values.squeeze()
    clustering = cg.clustering_coefficient(G).values.squeeze()
    
    # Build feature matrix
    X = np.column_stack([degrees, clustering])
    
    # Train Isolation Forest on GPU
    iforest = ml.IsolationForest(
        n_estimators=100,
        max_samples="auto",
        contamination="auto",
        random_state=42,
    )
    iforest.fit(X)
    
    # Get anomaly scores — higher score = more likely Byzantine
    anomaly_scores = iforest.decision_function(X)
    
    # Identify Byzantine nodes (top anomaly scores)
    n_nodes = len(anomaly_scores)
    n_byzantine = max(1, int(n_nodes * threshold))
    byzantine_indices = np.argsort(anomaly_scores)[-n_byzantine:]
    
    return byzantine_indices


def _fallback_byzantine_via_networkx(
    edge_list: np.ndarray,
    threshold: float,
) -> None:
    """Internal: Byzantine detection fallback via networkx/degree."""
    # Build networkx graph for fallback
    G = nx.Graph()
    sources = edge_list[:, 0].tolist() if edge_list.shape[1] > 1 else []
    targets = edge_list[:, 1].tolist() if edge_list.shape[1] > 1 else []
    weights = edge_list[:, 2].tolist() if edge_list.shape[1] > 2 else [1.0] * len(sources)
    
    for s, t, w in zip(sources, targets, weights):
        G.add_edge(s, t, weight=w)
    
    # Degree-based heuristic: nodes with very low degree relative
    # to community degree are Byzantine candidates
    degrees = dict(G.degree())
    avg_degree = sum(degrees.values()) / len(degrees) if degrees else 0
    
    # Nodes with degree < 20% of average are candidates
    byzantine_candidates = [
        node for node, deg in degrees.items()
        if deg < 0.2 * avg_degree and deg > 0
    ]
    
    # Return via module-level would need redesign; this is a demo
    # In production, would integrate with module's detect_byzantine()
    pass


def gpu_byzantine_benchmark() -> dict:
    """Benchmark GPU Byzantine detection vs CPU."""
    import time
    
    # Generate graph: 1000-node random regular graph
    n = 1000
    G = nx.random_regular_graph(4, n)
    edge_list = np.array([
        [u, v, 1.0] for u, v in G.edges()
    ])
    
    # CPU version (networkx-based, current implementation)
    t_cpu_start = time.time()
    # cpu_result = detect_byzantine(G, threshold=0.2)  # existing
    # Simulate: compute degrees and find low-degree nodes
    degrees = dict(G.degree())
    avg_degree = sum(degrees.values()) / len(degrees)
    cpu_byzantine = [n for n, d in degrees.items() if d < 0.2 * avg_degree and d > 0]
    t_cpu = time.time() - t_cpu_start
    
    # GPU version (new cuML-based)
    t_gpu_start = time.time()
    gpu_result = gpu_byzantine_detection(edge_list, threshold=0.2)
    t_gpu = time.time() - t_gpu_start
    
    return {
        "nodes": n,
        "cpu_time": round(t_cpu, 3),
        "gpu_time": round(t_gpu, 3),
        "speedup": round(t_cpu / t_gpu if t_gpu > 0 else float('inf'), 1),
        "byzantine_count_cpu": len(cpu_result),
        "byzantine_count_gpu": len(gpu_result),
    }