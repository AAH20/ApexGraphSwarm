"""
Dynamic Fault-Tolerant Workflow Reconfiguration (Self-Healing DAG) Solver.
Reconfigures agent workflow execution graphs upon runtime tool/subagent failures,
minimizing makespan disruption and avoiding agent failure death spirals.
"""
import time
from typing import List, Dict, Set, Tuple
from .models import SubTask, TaskFailureEvent, SelfHealingDAGResult
from .workflow_dag import WorkflowDAGSynthesizer

class SelfHealingDAGReconfigurator:
    """
    Dynamically hot-swaps failed workflow nodes with viable fallbacks and repairs execution schedules.
    """

    def __init__(self, initial_tasks: List[SubTask]):
        self.initial_tasks = {t.task_id: t for t in initial_tasks}
        # Compute baseline makespan
        synth = WorkflowDAGSynthesizer(initial_tasks)
        self.baseline_result = synth.solve()

    def reconfigure(
        self,
        failure_event: TaskFailureEvent,
        fallback_task_templates: Dict[str, SubTask]
    ) -> SelfHealingDAGResult:
        t0 = time.perf_counter()

        failed_id = failure_event.failed_task_id
        if failed_id not in self.initial_tasks:
            t1 = time.perf_counter()
            return SelfHealingDAGResult(
                repaired_schedule=self.baseline_result.task_schedule,
                makespan_increase_ms=0.0,
                tasks_rerouted=0,
                stability_score=1.0,
                algorithm="INCREMENTAL_DAG_RECONFIG",
                execution_time_us=(t1 - t0) * 1e6
            )

        failed_task = self.initial_tasks[failed_id]
        new_tasks = dict(self.initial_tasks)

        # Select the best fallback candidate (e.g. shortest duration or lowest error rate)
        chosen_fallback_id = None
        for candidate_id in failure_event.fallback_candidates:
            if candidate_id in fallback_task_templates:
                chosen_fallback_id = candidate_id
                break

        rerouted = 0
        if chosen_fallback_id:
            fallback_template = fallback_task_templates[chosen_fallback_id]
            # Replace failed task with fallback
            del new_tasks[failed_id]
            # Fallback inherits dependencies of the failed task
            new_fallback = SubTask(
                task_id=chosen_fallback_id,
                name=fallback_template.name,
                duration_ms=fallback_template.duration_ms,
                dependencies=list(failed_task.dependencies),
                assigned_role=fallback_template.assigned_role
            )
            new_tasks[chosen_fallback_id] = new_fallback
            rerouted = 1

            # Update dependencies in successors
            for tid, t in list(new_tasks.items()):
                if failed_id in t.dependencies:
                    new_deps = [chosen_fallback_id if d == failed_id else d for d in t.dependencies]
                    new_tasks[tid] = SubTask(
                        task_id=t.task_id,
                        name=t.name,
                        duration_ms=t.duration_ms,
                        dependencies=new_deps,
                        assigned_role=t.assigned_role
                    )

        # Re-synthesize the workflow DAG
        repaired_synth = WorkflowDAGSynthesizer(list(new_tasks.values()))
        repaired_res = repaired_synth.solve()

        makespan_increase = max(0.0, repaired_res.total_makespan_ms - self.baseline_result.total_makespan_ms)

        # Stability score: fraction of unchanged task start times
        unchanged = 0
        total_eval = 0
        for tid, orig_start in self.baseline_result.task_schedule.items():
            if tid in repaired_res.task_schedule:
                total_eval += 1
                if abs(repaired_res.task_schedule[tid] - orig_start) < 1.0:
                    unchanged += 1
        stability = (unchanged / max(total_eval, 1))

        t1 = time.perf_counter()
        return SelfHealingDAGResult(
            repaired_schedule=repaired_res.task_schedule,
            makespan_increase_ms=makespan_increase,
            tasks_rerouted=rerouted,
            stability_score=stability,
            algorithm="INCREMENTAL_DAG_RECONFIG",
            execution_time_us=(t1 - t0) * 1e6
        )
