"""
solid-name: RunCompletionChecker
solid-category: service
solid-spec: [SPEC-013]
solid-description: Determines whether a run has completed all steps, any step has exhausted attempts, or the time limit has been exceeded.
"""

from __future__ import annotations

from pathlib import Path

from harness.active_run_pointer_storing import ActiveRunPointerStoring
from harness.event_appender import EventAppending
from harness.flow_next_result import FlowNextResult
from harness.models import FlowDef, RunState
from harness.run_completion_checking import RunCompletionChecking


class RunCompletionChecker(RunCompletionChecking):

    def __init__(
        self,
        event_appender: EventAppending,
        active_run: ActiveRunPointerStoring,
    ) -> None:
        self._event_appender = event_appender
        self._active_run = active_run

    def check(
        self,
        base_dir: Path,
        run_id: str,
        events_path: str,
        flow_def: FlowDef,
        run_state: RunState,
    ) -> FlowNextResult | None:
        all_step_ids = {s.id for s in flow_def.steps}
        if all_step_ids.issubset(run_state.completed.keys()):
            self._event_appender.append(events_path, "run_completed", {"run_id": run_id})
            self._active_run.delete(base_dir)
            return FlowNextResult(status="done")

        exhausted_step_id = self._exhausted_step(flow_def, run_state)
        if exhausted_step_id is not None:
            self._event_appender.append(events_path, "run_failed", {"run_id": run_id, "step_id": exhausted_step_id})
            self._active_run.delete(base_dir)
            return FlowNextResult(status="failed")

        if run_state.turn_count >= flow_def.max_turns:
            self._event_appender.append(events_path, "run_timed_out", {"run_id": run_id})
            self._active_run.delete(base_dir)
            return FlowNextResult(status="timed_out")

        return None

    def _exhausted_step(self, flow_def: FlowDef, run_state: RunState) -> str | None:
        for step in flow_def.steps:
            if step.id in run_state.completed:
                continue
            if run_state.attempts_used.get(step.id, 0) >= step.max_attempts:
                return step.id
        return None