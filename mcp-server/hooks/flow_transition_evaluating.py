"""
solid-name: FlowTransitionGate
solid-category: service
solid-spec: [SPEC-014]
solid-description: Blocks turn endings while a flow run has pending steps.
solid-tags: [hook]
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

_MCP_DIR = Path(__file__).resolve().parents[1]
if str(_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(_MCP_DIR))

from harness.flow_status_reading import FlowStatusReading  # noqa: E402
from pending_step_failure_recording import PendingStepFailureRecording  # noqa: E402


class FlowTransitionGate:
    """Blocks ending a turn while a flow run is in_progress with a step still pending.

    Records each block as a failed attempt against the pending step so a stuck agent
    can't be blocked forever — once the step's own max_attempts is exhausted, the run
    is marked failed and this gate allows the turn to end.
    """

    def __init__(self, status_reader: FlowStatusReading, failure_recorder: PendingStepFailureRecording) -> None:
        self._status_reader = status_reader
        self._failure_recorder = failure_recorder

    def evaluate(self, run_id: Optional[str] = None) -> dict:
        status = self._status_reader.flow_status(run_id)
        if status.status != "in_progress" or not status.pending:
            return {"allow": True}

        terminal = self._failure_recorder.record(run_id, status.pending[0])
        if terminal is not None and terminal.error:
            return {"allow": False, "reason": terminal.error}

        reason = (
            f"Flow '{status.flow}' (run_id: {status.run_id}) has step(s) {status.pending} "
            "ready but not yet submitted. Call flow_next to advance the run before ending your turn — "
            "do not stop with a flow left in_progress."
        )
        return {"allow": False, "reason": reason}
