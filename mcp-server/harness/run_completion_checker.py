"""Coordinates terminal workflow-run state."""

from __future__ import annotations

from pathlib import Path

from harness.active_run_pointer_storing import ActiveRunPointerStoring
from harness.attempt_exhaustion_evaluating import AttemptExhaustionEvaluating
from harness.attempt_exhaustion_message_building import AttemptExhaustionMessageBuilding
from harness.event_appender import EventAppending
from harness.flow_next_result import FlowNextResult
from harness.models import FlowDef, RunState
from harness.run_completion_checking import RunCompletionChecking
from harness.run_timeout_message_building import RunTimeoutMessageBuilding


"""
solid-name: RunCompletionChecker
solid-category: service
solid-spec: [SPEC-031]
solid-description: Coordinates completed, exhausted, and timed-out workflow-run terminal states.
"""
class RunCompletionChecker(RunCompletionChecking):

    def __init__(
        self,
        event_appender: EventAppending,
        active_run: ActiveRunPointerStoring,
        exhaustion_evaluator: AttemptExhaustionEvaluating,
        exhaustion_message_builder: AttemptExhaustionMessageBuilding,
        timeout_message_builder: RunTimeoutMessageBuilding,
    ) -> None:
        self._event_appender = event_appender
        self._active_run = active_run
        self._exhaustion_evaluator = exhaustion_evaluator
        self._exhaustion_message_builder = exhaustion_message_builder
        self._timeout_message_builder = timeout_message_builder

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

        exhausted = self._exhaustion_evaluator.evaluate(flow_def, run_state)
        if exhausted is not None:
            self._event_appender.append(events_path, "run_failed", {
                "run_id": run_id,
                "step_id": exhausted.step_id,
                "attempt_id": exhausted.attempt_id,
            })
            self._active_run.delete(base_dir)
            return FlowNextResult(
                status="failed",
                error=self._exhaustion_message_builder.build(
                    exhausted,
                    run_state,
                    events_path,
                ),
            )

        if run_state.turn_count >= flow_def.max_turns:
            self._event_appender.append(events_path, "run_timed_out", {"run_id": run_id})
            self._active_run.delete(base_dir)
            return FlowNextResult(
                status="timed_out",
                error=self._timeout_message_builder.build(
                    flow_def,
                    run_state,
                    events_path,
                ),
            )

        return None
