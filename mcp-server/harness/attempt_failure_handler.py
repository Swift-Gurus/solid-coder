"""
solid-name: AttemptFailureHandler
solid-category: service
solid-spec: [SPEC-027]
solid-description: Handles all step failure types and determines the next flow action.
"""

from __future__ import annotations

from pathlib import Path

from harness.attempt_failure_handling import AttemptFailureHandling
from harness.event_appender import EventAppending
from harness.event_replaying import EventReplaying
from harness.flow_next_result import FlowNextResult
from harness.models import FlowDef
from harness.run_completion_checking import RunCompletionChecking


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
    ) -> FlowNextResult | None:
        event_type = "step_rejected" if reopen else "step_attempt_failed"
        self._event_appender.append(events_path, event_type, {"step_id": step_id, "reason": reason})
        run_state = self._event_replayer.replay(events_path)
        return self._completion_checker.check(base_dir, run_id, events_path, flow_def, run_state)
