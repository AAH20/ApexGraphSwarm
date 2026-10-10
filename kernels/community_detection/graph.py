"""Minimal graph representation for community detection kernels.

Supports dict-backed adjacency representations for O(1) neighbor lookups
and weighted degree computation. Compatible with incremental modularity
operations in this package.
"""

from __future__ import annotations

from typing import Dict, Hashable, Iterator, Optional


class Graph:
    """Weighted undirected graph backed by adjacency dicts.

    Args:
        adjacency: Mapping of node -> {neighbor: weight}. If None, empty graph.
    """

    def __init__(self, adjacency: Optional[Dict[Hashable, Dict[Hashable, float]]] = None):
        self._adj: Dict[Hashable, Dict[Hashable, float]] = adjacency or {}
        self._m: float = 0.0
        for u, neighbors in self._adj.items():
            for v, w in neighbors.items():
                if u <= v:
                    self._m += float(w)
        # Ensure all neighbors have entries
        for neighbors in self._adj.values():
            for v in neighbors:
                if v not in self._adj:
                    self._adj[v] = {}

    def nodes(self) -> Iterator[Hashable]:
        """Yield all nodes in the graph."""
        return iter(self._adj.keys())

    def neighbors(self, u: Hashable) -> Dict[Hashable, float]:
        """Return {neighbor: weight} for node u."""
        return self._adj.get(u, {})

    def weighted_degree(self, u: Hashable) -> float:
        """Sum of edge weights incident to u."""
        return sum(self._adj.get(u, {}).values())

    @property
    def m(self) -> float:
        """Total edge weight (sum of all undirected edges)."""
        return self._m

    @classmethod
    def from_edges(
        cls,
        edges: list,
    ) -> "Graph":
        """Build graph from edge list [(u, v, weight), ...]."""
        adj: Dict[Hashable, Dict[Hashable, float]] = {}
        for u, v, w in edges:
            adj.setdefault(u, {})[v] = float(w)
            adj.setdefault(v, {})[u] = float(w)
        return cls(adj)
