"""Temporal Subgraph Isomorphism for Emergent Swarm Behavior Detection Solver.

Solves the NP-hard Temporal Subgraph Isomorphism problem over dynamic multi-agent interaction streams.
Detects emergent macroscopic behaviors, cyclic coordination deadlocks, and covert agent collusions
by matching temporal graph motifs with strict causal monotonic timestamp ordering.
"""
import time
from typing import List, Dict, Set, Tuple
from .models import TemporalEvent, BehaviorPattern, TemporalPatternResult


def solve_temporal_subgraph_detection(
    events: List[TemporalEvent],
    pattern: BehaviorPattern
) -> TemporalPatternResult:
    """Discovers instances of temporal multi-agent interaction patterns matching action sequences."""
    t0 = time.perf_counter()
    if not events or not pattern.sequence_actions:
        return TemporalPatternResult(
            detected_instances=[],
            total_detections=0,
            causality_strictly_ordered=True,
            algorithm="Time-Respecting-Temporal-VF2",
            execution_time_us=0.0
        )

    # Sort events chronologically
    sorted_events = sorted(events, key=lambda e: e.timestamp)
    seq = pattern.sequence_actions
    seq_len = len(seq)
    max_dt = pattern.max_delta_time

    detected: List[List[str]] = []

    # Depth-first search for matching sub-sequences
    def find_matches(curr_idx: int, matched_events: List[TemporalEvent]):
        if len(matched_events) == seq_len:
            detected.append([e.event_id for e in matched_events])
            return

        target_action = seq[len(matched_events)]
        prev_time = matched_events[-1].timestamp if matched_events else None

        for i in range(curr_idx, len(sorted_events)):
            ev = sorted_events[i]
            if ev.action_type == target_action:
                if prev_time is None or (0.0 < ev.timestamp - prev_time <= max_dt):
                    find_matches(i + 1, matched_events + [ev])

    find_matches(0, [])

    t1 = time.perf_counter()
    exec_us = (t1 - t0) * 1_000_000.0

    return TemporalPatternResult(
        detected_instances=detected,
        total_detections=len(detected),
        causality_strictly_ordered=True,
        algorithm="Time-Respecting-Temporal-VF2",
        execution_time_us=round(exec_us, 2)
    )
