"""Property-based tests for execution_graph invariants using hypothesis."""
from __future__ import annotations

import json
from typing import Any

from hypothesis import given, settings, strategies as st

from apexgraphswarm.execution_graph import (
    DEFAULT_MAX_EDGES,
    DEFAULT_MAX_NODES,
    MAX_EDGES,
    MAX_NODES,
    project_execution_graph,
)


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_valid_id = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\x00"),
    min_size=1,
    max_size=64,
)

_nonnegative_int = st.integers(min_value=0, max_value=2**31 - 1)

_status = st.sampled_from([
    "pending", "claimed", "running", "succeeded", "failed",
    "cancelled", "blocked", "needs_reconciliation",
])

_task = st.fixed_dictionaries({
    "taskId": _valid_id,
    "id": _valid_id,
    "status": _status,
    "agentId": _valid_id,
    "reservedCostMicrousd": _nonnegative_int,
    "attempts": st.integers(min_value=0, max_value=10),
    "executionClass": _valid_id,
    "tool": _valid_id,
    "resource": _valid_id,
    "dependencies": st.lists(_valid_id, max_size=5),
})

_agent = st.fixed_dictionaries({
    "id": _valid_id,
    "name": st.text(max_size=128),
})

_attempt = st.fixed_dictionaries({
    "attemptId": _valid_id,
    "taskId": _valid_id,
    "attempt": st.integers(min_value=0, max_value=10),
    "outcome": st.sampled_from(["succeeded", "failed", "unknown"]),
    "actualCostMicrousd": st.one_of(st.none(), _nonnegative_int),
    "reservedMicrousd": st.one_of(st.none(), _nonnegative_int),
    "workerId": _valid_id,
    "principalId": _valid_id,
    "grantId": _valid_id,
    "tool": _valid_id,
    "resource": _valid_id,
    "startedAt": st.one_of(st.none(), st.floats(min_value=0, max_value=1e12, allow_nan=False, allow_infinity=False)),
    "settledAt": st.one_of(st.none(), st.floats(min_value=0, max_value=1e12, allow_nan=False, allow_infinity=False)),
})

_status_mapping = st.fixed_dictionaries({
    "run": st.fixed_dictionaries({
        "id": _valid_id,
        "status": _status,
        "budgetExceeded": st.booleans(),
        "cancelRequested": st.booleans(),
        "reservedMicrousd": st.one_of(st.none(), _nonnegative_int),
        "spentMicrousd": st.one_of(st.none(), _nonnegative_int),
        "budgetMicrousd": st.one_of(st.none(), _nonnegative_int),
        "remainingMicrousd": st.one_of(st.none(), _nonnegative_int),
        "version": st.integers(min_value=1, max_value=100),
    }),
    "tasks": st.lists(_task, max_size=20),
    "agents": st.lists(_agent, max_size=10),
})

_ledger = st.fixed_dictionaries({
    "attempts": st.lists(_attempt, max_size=20),
    "totalAttempts": st.integers(min_value=0, max_value=100),
    "returnedAttempts": st.integers(min_value=0, max_value=100),
    "knownActualMicrousd": st.one_of(st.none(), _nonnegative_int),
    "unresolvedCostCount": st.integers(min_value=0, max_value=100),
    "allCostsResolved": st.booleans(),
    "coverageComplete": st.booleans(),
    "truncated": st.booleans(),
})


# ---------------------------------------------------------------------------
# Graph structure invariants
# ---------------------------------------------------------------------------

class TestExecutionGraphStructure:
    """project_execution_graph always produces a well-formed graph."""

    @given(status=_status_mapping)
    @settings(max_examples=200, deadline=None)
    def test_output_is_valid_json_serializable(self, status: dict[str, Any]) -> None:
        result = project_execution_graph(status)
        encoded = json.dumps(result, allow_nan=False)
        assert isinstance(encoded, str)
        assert len(encoded) > 0

    @given(status=_status_mapping)
    @settings(max_examples=200, deadline=None)
    def test_version_is_always_one(self, status: dict[str, Any]) -> None:
        result = project_execution_graph(status)
        assert result["version"] == 1

    @given(status=_status_mapping)
    @settings(max_examples=200, deadline=None)
    def test_run_id_matches_input(self, status: dict[str, Any]) -> None:
        result = project_execution_graph(status)
        assert result["runId"] == status["run"]["id"]

    @given(status=_status_mapping)
    @settings(max_examples=200, deadline=None)
    def test_node_ids_are_unique(self, status: dict[str, Any]) -> None:
        result = project_execution_graph(status)
        ids = [node["id"] for node in result["nodes"]]
        assert len(ids) == len(set(ids))

    @given(status=_status_mapping)
    @settings(max_examples=200, deadline=None)
    def test_edge_endpoints_exist_in_nodes(self, status: dict[str, Any]) -> None:
        result = project_execution_graph(status)
        node_ids = {node["id"] for node in result["nodes"]}
        for edge in result["edges"]:
            assert edge["source"] in node_ids
            assert edge["target"] in node_ids

    @given(status=_status_mapping)
    @settings(max_examples=200, deadline=None)
    def test_edge_ids_are_unique(self, status: dict[str, Any]) -> None:
        result = project_execution_graph(status)
        edge_ids = [edge["id"] for edge in result["edges"]]
        assert len(edge_ids) == len(set(edge_ids))

    @given(status=_status_mapping)
    @settings(max_examples=200, deadline=None)
    def test_node_count_within_bounds(self, status: dict[str, Any]) -> None:
        result = project_execution_graph(status)
        assert 1 <= len(result["nodes"]) <= DEFAULT_MAX_NODES

    @given(status=_status_mapping)
    @settings(max_examples=200, deadline=None)
    def test_edge_count_within_bounds(self, status: dict[str, Any]) -> None:
        result = project_execution_graph(status)
        assert 0 <= len(result["edges"]) <= DEFAULT_MAX_EDGES

    @given(status=_status_mapping)
    @settings(max_examples=200, deadline=None)
    def test_summary_counts_match_actual(self, status: dict[str, Any]) -> None:
        result = project_execution_graph(status)
        summary = result["summary"]
        assert summary["nodeCount"] == len(result["nodes"])
        assert summary["edgeCount"] == len(result["edges"])

    @given(status=_status_mapping)
    @settings(max_examples=200, deadline=None)
    def test_limitations_are_present(self, status: dict[str, Any]) -> None:
        result = project_execution_graph(status)
        assert isinstance(result["limitations"], list)
        assert len(result["limitations"]) > 0

    @given(status=_status_mapping)
    @settings(max_examples=200, deadline=None)
    def test_truncated_flag_is_boolean(self, status: dict[str, Any]) -> None:
        result = project_execution_graph(status)
        assert isinstance(result["truncated"], bool)

    @given(status=_status_mapping)
    @settings(max_examples=50, deadline=None)
    def test_no_lease_tokens_leak(self, status: dict[str, Any]) -> None:
        """Lease tokens must never appear in the graph."""
        result = project_execution_graph(status)
        encoded = json.dumps(result)
        assert "leaseToken" not in encoded
        assert "lease_token" not in encoded

    @given(status=_status_mapping)
    @settings(max_examples=200, deadline=None)
    def test_run_node_always_present(self, status: dict[str, Any]) -> None:
        result = project_execution_graph(status)
        run_nodes = [n for n in result["nodes"] if n["kind"] == "run"]
        assert len(run_nodes) == 1
        assert run_nodes[0]["id"] == f"run:{status['run']['id']}"

    @given(status=_status_mapping)
    @settings(max_examples=200, deadline=None)
    def test_all_costs_resolved_is_boolean(self, status: dict[str, Any]) -> None:
        result = project_execution_graph(status)
        assert isinstance(result["summary"]["allCostsResolved"], bool)

    @given(status=_status_mapping)
    @settings(max_examples=200, deadline=None)
    def test_attempt_coverage_fields_present(self, status: dict[str, Any]) -> None:
        result = project_execution_graph(status)
        coverage = result["summary"]["attemptCoverage"]
        assert "expected" in coverage
        assert "recorded" in coverage
        assert "missing" in coverage
        assert "complete" in coverage
        assert isinstance(coverage["complete"], bool)


# ---------------------------------------------------------------------------
# Bounded parameter invariants
# ---------------------------------------------------------------------------

class TestExecutionGraphBounds:
    """Custom max_nodes/max_edges are respected."""

    @given(
        status=_status_mapping,
        max_nodes=st.integers(min_value=1, max_value=MAX_NODES),
        max_edges=st.integers(min_value=0, max_value=MAX_EDGES),
    )
    @settings(max_examples=100, deadline=None)
    def test_custom_bounds_respected(
        self, status: dict[str, Any], max_nodes: int, max_edges: int
    ) -> None:
        result = project_execution_graph(status, max_nodes=max_nodes, max_edges=max_edges)
        assert len(result["nodes"]) <= max_nodes
        assert len(result["edges"]) <= max_edges

    @given(
        status=_status_mapping,
        max_nodes=st.integers(min_value=1, max_value=MAX_NODES),
    )
    @settings(max_examples=100, deadline=None)
    def test_small_max_nodes_truncates(
        self, status: dict[str, Any], max_nodes: int
    ) -> None:
        result = project_execution_graph(status, max_nodes=max_nodes, max_edges=MAX_EDGES)
        assert len(result["nodes"]) <= max_nodes


# ---------------------------------------------------------------------------
# Ledger consistency invariants
# ---------------------------------------------------------------------------

class TestExecutionGraphLedger:
    """Ledger-derived summaries are consistent."""

    @given(status=_status_mapping, ledger=_ledger)
    @settings(max_examples=200, deadline=None)
    def test_ledger_attempts_produce_attempt_nodes(
        self, status: dict[str, Any], ledger: dict[str, Any]
    ) -> None:
        result = project_execution_graph(status, ledger=ledger)
        attempt_nodes = [n for n in result["nodes"] if n["kind"] == "attempt"]
        valid_attempts = [
            a for a in ledger["attempts"]
            if isinstance(a.get("taskId"), str) and a["taskId"] in {
                t["taskId"] for t in status["tasks"] if isinstance(t.get("taskId"), str)
            }
        ]
        assert len(attempt_nodes) <= len(valid_attempts)

    @given(status=_status_mapping, ledger=_ledger)
    @settings(max_examples=200, deadline=None)
    def test_known_actual_microusd_is_nonnegative(
        self, status: dict[str, Any], ledger: dict[str, Any]
    ) -> None:
        result = project_execution_graph(status, ledger=ledger)
        known = result["summary"]["knownActualMicrousd"]
        assert known is None or known >= 0

    @given(status=_status_mapping, ledger=_ledger)
    @settings(max_examples=200, deadline=None)
    def test_unknown_cost_attempts_is_nonnegative(
        self, status: dict[str, Any], ledger: dict[str, Any]
    ) -> None:
        result = project_execution_graph(status, ledger=ledger)
        assert result["summary"]["unknownCostAttempts"] >= 0


# ---------------------------------------------------------------------------
# Idempotence / determinism
# ---------------------------------------------------------------------------

class TestExecutionGraphDeterminism:
    """Same input always produces same output."""

    @given(status=_status_mapping)
    @settings(max_examples=100, deadline=None)
    def test_deterministic_output(self, status: dict[str, Any]) -> None:
        result1 = project_execution_graph(status)
        result2 = project_execution_graph(status)
        assert json.dumps(result1, sort_keys=True) == json.dumps(result2, sort_keys=True)

    @given(status=_status_mapping)
    @settings(max_examples=100, deadline=None)
    def test_deterministic_with_ledger(self, status: dict[str, Any]) -> None:
        ledger = {"attempts": [], "totalAttempts": 0}
        result1 = project_execution_graph(status, ledger=ledger)
        result2 = project_execution_graph(status, ledger=ledger)
        assert json.dumps(result1, sort_keys=True) == json.dumps(result2, sort_keys=True)
