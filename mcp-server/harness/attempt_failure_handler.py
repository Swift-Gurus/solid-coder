"""Handles failed workflow-step attempts."""

from __future__ import annotations

from pathlib import Path

from harness.attempt_failure import AttemptFailure
from harness.attempt_failure_handling import AttemptFailureHandling
from harness.event_appender import EventAppending
from harness.event_replaying import EventReplaying
from harness.flow_next_result import FlowNextResult
from harness.models import FlowDef
from harness.run_completion_checking import RunCompletionChecking


"""
solid-name: AttemptFailureHandler
solid-category: service
solid-spec: [SPEC-027]
solid-description: Records failed workflow-step attempts and evaluates terminal run state.
"""
class AttemptFailureHandler(AttemptFailureHandling):

    def __init__(
        self,
        event_appender: EventAppending,
        event_replayer: EventReplaying,
        completion_checker: RunCompletionChecking,
    ) -> None:
        self._event_appender = event_appender
        self._event_replayer = event_replayer
        self._completion_checker = completion_checker

    def handle(
        self,
        step_id: str,
        reason: str,
        reopen: bool,
        base_dir: Path,
        run_id: str,
        events_path: str,
        flow_def: FlowDef,
        attempt_id: str | None = None,
    ) -> FlowNextResult | None:
        return self.handle_all(
            failures=[
                AttemptFailure(
                    step_id=step_id,
                    reason=reason,
                    reopen=reopen,
                    attempt_id=attempt_id,
                )
            ],
            base_dir=base_dir,
            run_id=run_id,
            events_path=events_path,
            flow_def=flow_def,
        )

    def handle_all(
        self,
        failures: list[AttemptFailure],
        base_dir: Path,
        run_id: str,
        events_path: str,
        flow_def: FlowDef,
    ) -> FlowNextResult | None:
        if not failures:
            return None
        for failure in failures:
            event_type = "step_rejected" if failure.reopen else "step_attempt_failed"
            payload = {"step_id": failure.step_id, "reason": failure.reason}
            if failure.attempt_id is not None:
                payload["attempt_id"] = failure.attempt_id
            self._event_appender.append(events_path, event_type, payload)
        run_state = self._event_replayer.replay(events_path)
        return self._completion_checker.check(base_dir, run_id, events_path, flow_def, run_state)
