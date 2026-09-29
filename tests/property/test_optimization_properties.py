"""Property-based tests for optimization.schedule_dag invariants."""
from __future__ import annotations

from hypothesis import given, settings, strategies as st

from apexgraphswarm.optimization import (
    DagTask,
    ModelOption,
    OptimizationInputError,
    schedule_dag,
)


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_model_name = st.from_regex(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,31}', fullmatch=True)

_nonnegative_float = st.floats(min_value=0, max_value=1e6, allow_nan=False, allow_infinity=False)
_nonnegative_int = st.integers(min_value=0, max_value=2**31 - 1)

_model_option = st.builds(
    ModelOption,
    model=_model_name,
    estimated_cost_microusd=st.one_of(st.none(), _nonnegative_int),
    duration_estimate=_nonnegative_float,
    eligible=st.booleans(),
)


@st.composite
def _dag_tasks(draw, max_tasks: int = 6):
    """Generate a valid DAG: dependencies only reference earlier tasks."""
    n = draw(st.integers(min_value=0, max_value=max_tasks))
    ids = [f"t{i}" for i in range(n)]
    tasks = []
    for i, tid in enumerate(ids):
        possible_deps = ids[:i]
        if possible_deps:
            deps = draw(st.lists(st.sampled_from(possible_deps), max_size=min(3, len(possible_deps))))
            deps = list(dict.fromkeys(deps))
        else:
            deps = []
        options = draw(st.lists(_model_option, max_size=3))
        deadline = draw(st.one_of(st.none(), _nonnegative_float))
        tasks.append(DagTask(
            id=tid,
            dependencies=tuple(deps),
            duration_estimate=draw(_nonnegative_float),
            options=tuple(options),
            deadline=deadline,
        ))
    return tasks


# ---------------------------------------------------------------------------
# Schedule result invariants
# ---------------------------------------------------------------------------

class TestScheduleDagInvariants:
    """schedule_dag always returns a well-formed result."""

    @given(
        tasks=_dag_tasks(),
        budget=_nonnegative_int,
        capacities=st.dictionaries(_model_name, st.integers(min_value=0, max_value=100), max_size=5),
        deadline=st.one_of(st.none(), _nonnegative_float),
        model_options=st.lists(_model_option, max_size=5),
    )
    @settings(max_examples=200, deadline=None)
    def test_result_has_required_fields(
        self, tasks, budget, capacities, deadline, model_options
    ) -> None:
        result = schedule_dag(
            tasks,
            budget_microusd=budget,
            capacities=capacities,
            deadline_seconds=deadline,
            model_options=model_options,
        )
        assert result.status in ("feasible", "infeasible", "unknown")
        assert isinstance(result.exact, bool)
        assert isinstance(result.algorithm, str)

    @given(
        tasks=_dag_tasks(),
        budget=_nonnegative_int,
        capacities=st.dictionaries(_model_name, st.integers(min_value=0, max_value=100), max_size=5),
        deadline=st.one_of(st.none(), _nonnegative_float),
        model_options=st.lists(_model_option, max_size=5),
    )
    @settings(max_examples=200, deadline=None)
    def test_feasible_schedule_respects_budget(
        self, tasks, budget, capacities, deadline, model_options
    ) -> None:
        result = schedule_dag(
            tasks,
            budget_microusd=budget,
            capacities=capacities,
            deadline_seconds=deadline,
            model_options=model_options,
        )
        if result.feasible and result.total_cost_microusd is not None:
            assert result.total_cost_microusd <= budget

    @given(
        tasks=_dag_tasks(),
        budget=_nonnegative_int,
        capacities=st.dictionaries(_model_name, st.integers(min_value=0, max_value=100), max_size=5),
        deadline=st.one_of(st.none(), _nonnegative_float),
        model_options=st.lists(_model_option, max_size=5),
    )
    @settings(max_examples=200, deadline=None)
    def test_feasible_schedule_assigns_all_tasks(
        self, tasks, budget, capacities, deadline, model_options
    ) -> None:
        result = schedule_dag(
            tasks,
            budget_microusd=budget,
            capacities=capacities,
            deadline_seconds=deadline,
            model_options=model_options,
        )
        if result.feasible and tasks:
            assigned_ids = {a.task_id for a in result.assignments}
            assert assigned_ids == {t.id for t in tasks}

    @given(
        tasks=_dag_tasks(),
        budget=_nonnegative_int,
        capacities=st.dictionaries(_model_name, st.integers(min_value=0, max_value=100), max_size=5),
        deadline=st.one_of(st.none(), _nonnegative_float),
        model_options=st.lists(_model_option, max_size=5),
    )
    @settings(max_examples=200, deadline=None)
    def test_makespan_is_max_finish(
        self, tasks, budget, capacities, deadline, model_options
    ) -> None:
        result = schedule_dag(
            tasks,
            budget_microusd=budget,
            capacities=capacities,
            deadline_seconds=deadline,
            model_options=model_options,
        )
        if result.feasible and result.assignments:
            computed_makespan = max(a.finish for a in result.assignments)
            assert abs(result.makespan - computed_makespan) < 1e-9

    @given(
        tasks=_dag_tasks(),
        budget=_nonnegative_int,
        capacities=st.dictionaries(_model_name, st.integers(min_value=0, max_value=100), max_size=5),
        deadline=st.one_of(st.none(), _nonnegative_float),
        model_options=st.lists(_model_option, max_size=5),
    )
    @settings(max_examples=200, deadline=None)
    def test_total_cost_matches_assignments(
        self, tasks, budget, capacities, deadline, model_options
    ) -> None:
        result = schedule_dag(
            tasks,
            budget_microusd=budget,
            capacities=capacities,
            deadline_seconds=deadline,
            model_options=model_options,
        )
        if result.feasible and result.assignments:
            computed_cost = sum(a.cost_microusd for a in result.assignments)
            assert result.total_cost_microusd == computed_cost

    @given(
        budget=_nonnegative_int,
        capacities=st.dictionaries(_model_name, st.integers(min_value=0, max_value=100), max_size=5),
        deadline=st.one_of(st.none(), _nonnegative_float),
        model_options=st.lists(_model_option, max_size=5),
    )
    @settings(max_examples=50, deadline=None)
    def test_empty_dag_is_feasible_with_zero_cost(
        self, budget, capacities, deadline, model_options
    ) -> None:
        result = schedule_dag(
            [],
            budget_microusd=budget,
            capacities=capacities,
            deadline_seconds=deadline,
            model_options=model_options,
        )
        assert result.feasible is True
        assert result.total_cost_microusd == 0
        assert result.makespan == 0.0
        assert len(result.assignments) == 0

    @given(
        tasks=_dag_tasks(),
        budget=_nonnegative_int,
        capacities=st.dictionaries(_model_name, st.integers(min_value=0, max_value=100), max_size=5),
        deadline=st.one_of(st.none(), _nonnegative_float),
        model_options=st.lists(_model_option, max_size=5),
    )
    @settings(max_examples=100, deadline=None)
    def test_deterministic_output(
        self, tasks, budget, capacities, deadline, model_options
    ) -> None:
        result1 = schedule_dag(
            tasks,
            budget_microusd=budget,
            capacities=capacities,
            deadline_seconds=deadline,
            model_options=model_options,
        )
        result2 = schedule_dag(
            tasks,
            budget_microusd=budget,
            capacities=capacities,
            deadline_seconds=deadline,
            model_options=model_options,
        )
        assert result1.status == result2.status
        assert result1.total_cost_microusd == result2.total_cost_microusd
        assert result1.makespan == result2.makespan
        assert len(result1.assignments) == len(result2.assignments)


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

class TestScheduleDagValidation:
    """Invalid inputs raise OptimizationInputError."""

    @given(
        tasks=_dag_tasks(),
        budget=st.integers(min_value=-1000, max_value=-1),
        capacities=st.dictionaries(_model_name, st.integers(min_value=0, max_value=100), max_size=5),
        deadline=st.one_of(st.none(), _nonnegative_float),
        model_options=st.lists(_model_option, max_size=5),
    )
    @settings(max_examples=50, deadline=None)
    def test_negative_budget_raises(
        self, tasks, budget, capacities, deadline, model_options
    ) -> None:
        try:
            schedule_dag(
                tasks,
                budget_microusd=budget,
                capacities=capacities,
                deadline_seconds=deadline,
                model_options=model_options,
            )
        except (OptimizationInputError, ValueError):
            pass

    @given(
        tasks=_dag_tasks(),
        budget=_nonnegative_int,
        capacities=st.dictionaries(_model_name, st.integers(min_value=0, max_value=100), max_size=5),
        deadline=st.one_of(st.none(), _nonnegative_float),
        model_options=st.lists(_model_option, max_size=5),
        exact_max_tasks=st.one_of(
            st.integers(min_value=-100, max_value=0),
            st.integers(min_value=9, max_value=100),
        ),
    )
    @settings(max_examples=50, deadline=None)
    def test_invalid_exact_max_tasks_raises(
        self, tasks, budget, capacities, deadline, model_options, exact_max_tasks
    ) -> None:
        try:
            schedule_dag(
                tasks,
                budget_microusd=budget,
                capacities=capacities,
                deadline_seconds=deadline,
                model_options=model_options,
                exact_max_tasks=exact_max_tasks,
            )
        except (OptimizationInputError, ValueError):
            pass
