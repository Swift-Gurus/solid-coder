"""
solid-name: PendingStepFailureRecorder
solid-category: service
solid-tags: [hook]
solid-description: Records a step that was never submitted as a failed attempt.
"""

from __future__ import annotations

import sys
from pathlib import Path

_MCP_DIR = Path(__file__).resolve().parents[1]
if str(_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(_MCP_DIR))

from harness.active_run_locating import ActiveRunLocating
from harness.attempt_failure_handling import AttemptFailureHandling
from harness.flow_loading import FlowLoading
from harness.flow_next_result import FlowNextResult


class PendingStepFailureRecorder:
    def __init__(
        self,
        run_locator: ActiveRunLocating,
        flow_loader: FlowLoading,
        attempt_failure_handler: AttemptFailureHandling,
    ) -> None:
        self._run_locator = run_locator
        self._flow_loader = flow_loader
        self._attempt_failure_handler = attempt_failure_handler

    def record(self, run_id: str | None, step_id: str) -> FlowNextResult | None:
        location = self._run_locator.locate(run_id)
        flow_def = self._flow_loader.load(location.workflow_path, [])
        return self._attempt_failure_handler.handle(
            step_id=step_id,
            reason="Agent ended its turn without calling flow_next to submit this step.",
            reopen=False,
            base_dir=location.base_dir,
            run_id=location.run_id,
            events_path=location.events_path,
            flow_def=flow_def,
        )
