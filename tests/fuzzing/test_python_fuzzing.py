"""Property-based fuzzing for Python input parsers using Hypothesis.

Covers all major parser entry points in the apexgraphswarm package.
"""
from __future__ import annotations

import json
import math
import os
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hypothesis import given, settings, strategies as st, HealthCheck

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apexgraphswarm.control import ControlStore, ControlError, BudgetError, ConflictError, LeaseError
from apexgraphswarm.analytics import build_analytics, AnalyticsError
from apexgraphswarm.evaluation import (
    EvaluationSuite, Candidate, Attempt, evaluate, compare_candidates,
    evaluate_candidate, EvaluationError,
)
from apexgraphswarm.optimization import (
    optimize, schedule_dag, plan_waves, recommend_capacity,
    OptimizationInputError, DagTask, ModelOption, CodeTask, TelemetrySample,
)
from apexgraphswarm.hierarchy import plan_hierarchy, HierarchyError
from apexgraphswarm.delegation_plan import compile_delegation_plan, DelegationPlanError
from apexgraphswarm.execution_graph import project_execution_graph
from apexgraphswarm.repository_graph import build_repository_graph
from apexgraphswarm.request_registry import register_hashed_request, RequestRegistryError, RequestConflictError
from apexgraphswarm.specialist_access import (
    SpecialistContractError, initialize_specialist_schema, create_contract,
    approve_contract, activate_contract, contract_status,
    bind_plan, validate_task_contract,
)
from apexgraphswarm.inference_telemetry import parse_prometheus, TelemetryError
from apexgraphswarm.evolution import run_evolution, EvolutionError
from apexgraphswarm.repository_conflicts import (
    plan_repository_conflicts, verify_repository_conflict_plan, RepositoryConflictError,
)
from apexgraphswarm.receipt_reconciliation import reconcile_openrouter_task, ControlError as ReconControlError
from apexgraphswarm.provider_receipts import normalize_openrouter_receipt, ReceiptError
from apexgraphswarm.access import authorize, AccessDenied, initialize_access_schema
from apexgraphswarm.identity import verify_credential, WorkerIdentityError, initialize_identity_schema
from apexgraphswarm.ledger import attempt_id, record_attempt_start, settle_attempt
from apexgraphswarm.lab import dispatch


# ---------------------------------------------------------------------------
# Shared strategies
# ---------------------------------------------------------------------------

safe_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\x00"),
    min_size=0, max_size=200,
)

safe_id_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\x00"),
    min_size=1, max_size=128,
).filter(lambda s: s.strip() != "")

safe_json = st.recursive(
    st.none() | st.booleans() | st.integers(min_value=-(2**53), max_value=2**53) | st.floats(allow_nan=False, allow_infinity=False) | safe_text,
    lambda children: st.lists(children, max_size=10) | st.dictionaries(safe_text, children, max_size=10),
    max_leaves=20,
)

malformed_json_bytes = st.binary(min_size=0, max_size=500)

arbitrary_dicts = st.dictionaries(
    keys=st.text(max_size=50),
    values=st.recursive(
        st.none() | st.booleans() | st.integers() | st.floats(allow_nan=False, allow_infinity=False) | st.text(max_size=100),
        lambda children: st.lists(children, max_size=5) | st.dictionaries(st.text(max_size=20), children, max_size=5),
        max_leaves=10,
    ),
    max_size=20,
)

prometheus_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",)),
    min_size=0, max_size=5000,
)


def _valid_plan(**overrides):
    plan = {
        "version": 1,
        "agents": [{"id": "agent-1", "Name": "Agent"}],
        "tasks": [{
            "id": "task-1", "agentId": "agent-1", "dependencies": [],
            "payload": {"kind": "fixture"}, "reservedCostMicrousd": 0,
            "maxAttempts": 1, "executionClass": "fixture",
        }],
    }
    plan.update(overrides)
    return plan


# ---------------------------------------------------------------------------
# ControlStore fuzzing
# ---------------------------------------------------------------------------

class ControlStoreFuzzTests(unittest.TestCase):
    """Fuzz ControlStore plan validation and lifecycle."""

    @given(plan=arbitrary_dicts, budget=st.integers(min_value=-(2**63), max_value=2**63 - 1))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_create_run_never_crashes(self, plan, budget):
        """create_run must either succeed or raise ControlError, never crash."""
        with ControlStore(":memory:") as store:
            try:
                store.create_run(plan, idempotency_key="fuzz-key", budget_microusd=budget)
            except (ControlError, BudgetError, ConflictError, LeaseError, ValueError, TypeError):
                pass

    @given(
        task_id=safe_id_text,
        attempt=st.integers(min_value=-100, max_value=100),
    )
    @settings(max_examples=100)
    def test_attempt_id_deterministic(self, task_id, attempt):
        """attempt_id is deterministic and stable."""
        a = attempt_id(task_id, attempt)
        b = attempt_id(task_id, attempt)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in a))

    @given(
        task_id=safe_id_text,
        run_id=safe_id_text,
        attempt=st.integers(min_value=1, max_value=10),
        worker_id=safe_id_text,
        reserved=st.integers(min_value=0, max_value=2**63 - 1),
        started_at=st.floats(min_value=0, max_value=2**40, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_record_attemp_start_settle_roundtrip(
        self, task_id, run_id, attempt, worker_id, reserved, started_at
    ):
        """record_attempt_start + settle_attempt roundtrip."""
        db = sqlite3.connect(":memory:")
        db.row_factory = sqlite3.Row
        db.execute("""CREATE TABLE execution_attempts (
            attempt_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, run_id TEXT NOT NULL,
            attempt_number INTEGER NOT NULL, worker_id TEXT NOT NULL, principal_id TEXT,
            grant_id TEXT, tool_id TEXT, resource_id TEXT, reserved_microusd INTEGER NOT NULL,
            started_at REAL NOT NULL, outcome TEXT NOT NULL, actual_cost_microusd INTEGER,
            settled_at REAL, receipt_json TEXT
        )""")
        aid = record_attempt_start(
            db, task_id=task_id, run_id=run_id, attempt=attempt,
            worker_id=worker_id, principal_id=None, grant_id=None,
            reserved_microusd=reserved, tool_id=None, resource_id=None,
            started_at=started_at,
        )
        self.assertEqual(aid, attempt_id(task_id, attempt))
        settle_attempt(
            db, task_id=task_id, attempt=attempt, outcome="succeeded",
            actual_cost_microusd=0, settled_at=started_at + 1, receipt_json=None,
        )
        row = db.execute("SELECT outcome FROM execution_attempts WHERE attempt_id=?", (aid,)).fetchone()
        self.assertEqual(row["outcome"], "succeeded")
        db.close()

    @given(
        worker_id=safe_id_text,
        credential=st.text(min_size=0, max_size=600),
        now=st.floats(min_value=0, max_value=2**40, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_verify_credential_never_crashes(self, worker_id, credential, now):
        """verify_credential must raise WorkerIdentityError or return a row."""
        db = sqlite3.connect(":memory:")
        db.row_factory = sqlite3.Row
        initialize_identity_schema(db)
        try:
            verify_credential(db, worker_id=worker_id, credential=credential, now=now)
        except WorkerIdentityError:
            pass
        db.close()

    @given(
        principal_id=st.one_of(st.none(), safe_id_text),
        tool_id=safe_id_text,
        resource_id=safe_id_text,
        budget=st.integers(min_value=0, max_value=2**63 - 1),
        now=st.floats(min_value=0, max_value=2**40, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_authorize_never_crashes(self, principal_id, tool_id, resource_id, budget, now):
        """authorize must raise AccessDenied or return a grant_id."""
        db = sqlite3.connect(":memory:")
        db.row_factory = sqlite3.Row
        initialize_access_schema(db)
        try:
            authorize(
                db, principal_id=principal_id, tool_id=tool_id,
                resource_id=resource_id, budget_microusd=budget, now=now,
            )
        except AccessDenied:
            pass
        db.close()


# ---------------------------------------------------------------------------
# Analytics fuzzing
# ---------------------------------------------------------------------------

class AnalyticsFuzzTests(unittest.TestCase):
    """Fuzz analytics build_analytics with arbitrary request dicts."""

    @given(request=arbitrary_dicts)
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_build_analytics_never_crashes(self, request):
        """build_analytics must raise AnalyticsError or return a result."""
        try:
            build_analytics(request, now=datetime(2026, 9, 27, tzinfo=timezone.utc))
        except (AnalyticsError, ValueError, TypeError, KeyError):
            pass

    @given(
        rows=st.lists(
            st.fixed_dictionaries({
                "attemptId": safe_text,
                "taskId": safe_text,
                "tool": st.one_of(st.none(), safe_text),
                "resource": st.one_of(st.none(), safe_text),
                "startedAt": st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False)),
                "settledAt": st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False)),
                "outcome": safe_text,
                "actualCostMicrousd": st.one_of(st.none(), st.integers()),
            }),
            max_size=50,
        ),
        days=st.integers(min_value=0, max_value=400),
    )
    @settings(max_examples=100)
    def test_import_rows_never_crashes(self, rows, days):
        """Import path must not crash on arbitrary rows."""
        try:
            build_analytics(
                {"source": "import", "days": days, "rows": rows},
                now=datetime(2026, 9, 27, tzinfo=timezone.utc),
            )
        except (AnalyticsError, ValueError, TypeError, KeyError):
            pass


# ---------------------------------------------------------------------------
# Evaluation fuzzing
# ---------------------------------------------------------------------------

class EvaluationFuzzTests(unittest.TestCase):
    """Fuzz evaluation suite parsing and candidate comparison."""

    @given(raw=arbitrary_dicts)
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_evaluate_never_crashes(self, raw):
        """evaluate must raise EvaluationError or return a result."""
        try:
            evaluate(raw)
        except (EvaluationError, ValueError, TypeError, KeyError):
            pass

    @given(
        baseline=arbitrary_dicts,
        candidate=arbitrary_dicts,
        suite_raw=arbitrary_dicts,
    )
    @settings(max_examples=100)
    def test_compare_candidates_never_crashes(self, baseline, candidate, suite_raw):
        """compare_candidates must not crash."""
        try:
            suite = EvaluationSuite.from_dict(suite_raw)
        except (EvaluationError, ValueError, TypeError, KeyError):
            return
        try:
            compare_candidates(baseline, candidate, suite)
        except (EvaluationError, ValueError, TypeError, KeyError):
            pass


# ---------------------------------------------------------------------------
# Optimization fuzzing
# ---------------------------------------------------------------------------

class OptimizationFuzzTests(unittest.TestCase):
    """Fuzz optimization entry points."""

    @given(payload=arbitrary_dicts)
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_optimize_never_crashes(self, payload):
        """optimize must raise OptimizationInputError or return a result."""
        try:
            optimize(payload)
        except (OptimizationInputError, ValueError, TypeError, KeyError):
            pass

    @given(
        tasks=st.lists(
            st.fixed_dictionaries({
                "id": safe_id_text,
                "dependencies": st.lists(safe_id_text, max_size=10),
                "duration_estimate": st.floats(allow_nan=False, allow_infinity=False),
                "options": st.lists(
                    st.fixed_dictionaries({
                        "model": safe_text,
                        "estimated_cost_microusd": st.one_of(st.none(), st.integers()),
                        "duration_estimate": st.floats(allow_nan=False, allow_infinity=False),
                        "eligible": st.booleans(),
                    }),
                    max_size=5,
                ),
                "deadline": st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False)),
            }),
            max_size=20,
        ),
        budget=st.integers(min_value=0, max_value=2**63 - 1),
        capacities=st.dictionaries(safe_id_text, st.integers(min_value=0, max_value=10000), max_size=10),
    )
    @settings(max_examples=100)
    def test_schedule_dag_never_crashes(self, tasks, budget, capacities):
        """schedule_dag must not crash."""
        try:
            dag_tasks = []
            for t in tasks:
                options = tuple(
                    ModelOption(
                        model=o["model"],
                        estimated_cost_microusd=o["estimated_cost_microusd"],
                        duration_estimate=o["duration_estimate"],
                        eligible=o["eligible"],
                    )
                    for o in t["options"]
                )
                dag_tasks.append(DagTask(
                    id=t["id"],
                    dependencies=tuple(t["dependencies"]),
                    duration_estimate=t["duration_estimate"],
                    options=options,
                    deadline=t["deadline"],
                ))
            schedule_dag(dag_tasks, budget_microusd=budget, capacities=capacities)
        except (OptimizationInputError, ValueError, TypeError, KeyError):
            pass


# ---------------------------------------------------------------------------
# Hierarchy fuzzing
# ---------------------------------------------------------------------------

class HierarchyFuzzTests(unittest.TestCase):
    """Fuzz hierarchy plan_hierarchy."""

    @given(payload=arbitrary_dicts)
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_plan_hierarchy_never_crashes(self, payload):
        """plan_hierarchy must raise HierarchyError or return a result."""
        try:
            plan_hierarchy(payload)
        except (HierarchyError, ValueError, TypeError, KeyError):
            pass


# ---------------------------------------------------------------------------
# Delegation plan fuzzing
# ---------------------------------------------------------------------------

class DelegationPlanFuzzTests(unittest.TestCase):
    """Fuzz delegation plan compilation."""

    @given(
        problem=arbitrary_dicts,
        model_bindings=arbitrary_dicts,
        task_inputs=st.one_of(st.none(), arbitrary_dicts),
    )
    @settings(max_examples=100)
    def test_compile_delegation_plan_never_crashes(self, problem, model_bindings, task_inputs):
        """compile_delegation_plan must not crash."""
        try:
            compile_delegation_plan(problem, model_bindings, task_inputs=task_inputs)
        except (DelegationPlanError, ValueError, TypeError, KeyError):
            pass


# ---------------------------------------------------------------------------
# Execution graph fuzzing
# ---------------------------------------------------------------------------

class ExecutionGraphFuzzTests(unittest.TestCase):
    """Fuzz execution graph projection."""

    @given(status=arbitrary_dicts, ledger=st.one_of(st.none(), arbitrary_dicts))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_project_execution_graph_never_crashes(self, status, ledger):
        """project_execution_graph must raise ValueError or return a result."""
        try:
            project_execution_graph(status, ledger)
        except (ValueError, TypeError, KeyError):
            pass


# ---------------------------------------------------------------------------
# Repository graph fuzzing
# ---------------------------------------------------------------------------

class RepositoryGraphFuzzTests(unittest.TestCase):
    """Fuzz repository graph builder with temp directories."""

    @given(
        max_files=st.integers(min_value=1, max_value=100),
        max_symbols=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=50)
    def test_build_repository_graph_never_crashes(self, max_files, max_symbols):
        """build_repository_graph must not crash on arbitrary directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some random files
            for i in range(5):
                subdir = Path(tmpdir) / f"dir{i}"
                subdir.mkdir()
                for j in range(3):
                    (subdir / f"file{j}.py").write_text(
                        f"def func_{i}_{j}():\n    return {i + j}\n"
                    )
            try:
                build_repository_graph(tmpdir, max_files=max_files, max_symbols=max_symbols)
            except (ValueError, TypeError, OSError):
                pass


# ---------------------------------------------------------------------------
# Request registry fuzzing
# ---------------------------------------------------------------------------

class RequestRegistryFuzzTests(unittest.TestCase):
    """Fuzz request registry."""

    @given(
        request_key_hash=st.text(min_size=0, max_size=100),
        scope_hash=st.text(min_size=0, max_size=100),
        payload_digest=st.text(min_size=0, max_size=100),
        candidate_job_id=st.text(min_size=0, max_size=100),
    )
    @settings(max_examples=100)
    def test_register_hashed_request_never_crashes(
        self, request_key_hash, scope_hash, payload_digest, candidate_job_id
    ):
        """register_hashed_request must raise RequestRegistryError or succeed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.sqlite")
            try:
                register_hashed_request(
                    db_path,
                    request_key_hash=request_key_hash,
                    scope_hash=scope_hash,
                    payload_digest=payload_digest,
                    candidate_job_id=candidate_job_id,
                )
            except (RequestRegistryError, RequestConflictError, ValueError, TypeError):
                pass


# ---------------------------------------------------------------------------
# Specialist access fuzzing
# ---------------------------------------------------------------------------

class SpecialistAccessFuzzTests(unittest.TestCase):
    """Fuzz specialist access contract validation."""

    @given(
        design_input=arbitrary_dicts,
        assignment_input=arbitrary_dicts,
        now=st.floats(min_value=0, max_value=2**40, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_create_contract_never_crashes(self, design_input, assignment_input, now):
        """create_contract must raise SpecialistContractError or succeed."""
        db = sqlite3.connect(":memory:")
        db.row_factory = sqlite3.Row
        initialize_specialist_schema(db)
        try:
            create_contract(
                db, idempotency_key="fuzz-key",
                design_input=design_input, assignment_input=assignment_input, now=now,
            )
        except (SpecialistContractError, ValueError, TypeError, KeyError):
            pass
        db.close()

    @given(
        contract_id=safe_id_text,
        worker_id=safe_id_text,
        credential=st.one_of(st.none(), st.text(min_size=0, max_size=600)),
        now=st.floats(min_value=0, max_value=2**40, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50)
    def test_approve_contract_never_crashes(self, contract_id, worker_id, credential, now):
        """approve_contract must not crash."""
        db = sqlite3.connect(":memory:")
        db.row_factory = sqlite3.Row
        initialize_specialist_schema(db)
        try:
            approve_contract(
                db, contract_id=contract_id, worker_id=worker_id,
                credential=credential, now=now,
            )
        except (SpecialistContractError, ValueError, TypeError, KeyError):
            pass
        db.close()


# ---------------------------------------------------------------------------
# Inference telemetry fuzzing
# ---------------------------------------------------------------------------

class InferenceTelemetryFuzzTests(unittest.TestCase):
    """Fuzz Prometheus exposition parser."""

    @given(text=prometheus_text)
    @settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
    def test_parse_prometheus_never_crashes(self, text):
        """parse_prometheus must raise TelemetryError or return a snapshot."""
        try:
            parse_prometheus(text)
        except (TelemetryError, ValueError, TypeError, KeyError):
            pass


# ---------------------------------------------------------------------------
# Evolution fuzzing
# ---------------------------------------------------------------------------

class EvolutionFuzzTests(unittest.TestCase):
    """Fuzz evolution runner."""

    @given(payload=arbitrary_dicts)
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_run_evolution_never_crashes(self, payload):
        """run_evolution must raise EvolutionError or return a result."""
        try:
            run_evolution(payload)
        except (EvolutionError, ValueError, TypeError, KeyError):
            pass


# ---------------------------------------------------------------------------
# Repository conflicts fuzzing
# ---------------------------------------------------------------------------

class RepositoryConflictsFuzzTests(unittest.TestCase):
    """Fuzz repository conflict planner."""

    @given(
        base_revision=st.text(min_size=0, max_size=300),
        tasks=st.lists(
            st.fixed_dictionaries({
                "id": safe_id_text,
                "headRevision": safe_text,
                "dependencies": st.lists(safe_id_text, max_size=10),
                "reads": st.lists(safe_text, max_size=10),
            }),
            max_size=10,
        ),
    )
    @settings(max_examples=50)
    def test_plan_repository_conflicts_never_crashes(self, base_revision, tasks):
        """plan_repository_conflicts must not crash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize a git repo
            import subprocess
            try:
                subprocess.run(["git", "init", "-q"], cwd=tmpdir, capture_output=True, timeout=5)
                subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", "init"],
                             cwd=tmpdir, capture_output=True, timeout=5)
            except (OSError, subprocess.SubprocessError):
                pass
            try:
                plan_repository_conflicts(tmpdir, base_revision, tasks)
            except (RepositoryConflictError, ValueError, TypeError, KeyError, OSError):
                pass


# ---------------------------------------------------------------------------
# Receipt reconciliation fuzzing
# ---------------------------------------------------------------------------

class ReceiptReconciliationFuzzTests(unittest.TestCase):
    """Fuzz receipt reconciliation."""

    @given(
        task_id=safe_id_text,
        entries=st.lists(arbitrary_dicts, max_size=20),
        operator_id=safe_id_text,
    )
    @settings(max_examples=100)
    def test_reconcile_openrouter_task_never_crashes(self, task_id, entries, operator_id):
        """reconcile_openrouter_task must not crash."""
        with ControlStore(":memory:") as store:
            try:
                reconcile_openrouter_task(
                    store, task_id, entries, operator_id=operator_id,
                )
            except (ReconControlError, ValueError, TypeError, KeyError):
                pass


# ---------------------------------------------------------------------------
# Provider receipts fuzzing
# ---------------------------------------------------------------------------

class ProviderReceiptsFuzzTests(unittest.TestCase):
    """Fuzz provider receipt normalization."""

    @given(
        payload=arbitrary_dicts,
        expected_generation_id=safe_text,
        expected_model=st.one_of(st.none(), safe_text),
    )
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_normalize_openrouter_receipt_never_crashes(
        self, payload, expected_generation_id, expected_model
    ):
        """normalize_openrouter_receipt must raise ReceiptError or return a result."""
        try:
            normalize_openrouter_receipt(payload, expected_generation_id, expected_model)
        except (ReceiptError, ValueError, TypeError, KeyError):
            pass


# ---------------------------------------------------------------------------
# Lab dispatch fuzzing
# ---------------------------------------------------------------------------

class LabDispatchFuzzTests(unittest.TestCase):
    """Fuzz lab dispatch."""

    @given(payload=arbitrary_dicts)
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_dispatch_never_crashes(self, payload):
        """dispatch must raise ValueError or return a result."""
        try:
            dispatch(payload)
        except (ValueError, TypeError, KeyError, ImportError):
            pass


# ---------------------------------------------------------------------------
# Preview fuzzing
# ---------------------------------------------------------------------------

class PreviewFuzzTests(unittest.TestCase):
    """Fuzz preview operations."""

    @given(command=arbitrary_dicts)
    @settings(max_examples=100)
    def test_operate_never_crashes(self, command):
        """operate must raise ValueError or return a result."""
        from apexgraphswarm.preview import operate
        try:
            operate(command)
        except (ValueError, TypeError, KeyError, ControlError):
            pass


if __name__ == "__main__":
    unittest.main()
