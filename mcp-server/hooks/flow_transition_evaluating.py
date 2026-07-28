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


def build_default_flow_transition_gate(base_dir_resolver=None) -> FlowTransitionGate:
    """Wire a FlowTransitionGate against the real filesystem, using production defaults.

    `base_dir_resolver` defaults to the real project's runs directory; tests may override
    it to point at a temp directory instead.
    """
    from harness.active_run_locator import ActiveRunLocator
    from harness.active_run_pointer_store import ActiveRunPointerStore
    from harness.attempt_failure_handler import AttemptFailureHandler
    from harness.flow_engine_assembly import build_default_assembly
    from harness.flow_file_resolver import FlowFileResolver
    from harness.flow_status_reader import FlowStatusReader
    from harness.name_resolving_flow_loader import NameResolvingFlowLoader
    from harness.path_checking import PathChecker
    from harness.run_completion_checker import RunCompletionChecker
    from harness.run_context_builder import RunContextBuilder
    from harness.run_snapshot_resolver import RunSnapshotResolver
    from harness.runs_base_dir_resolver import RunsBaseDirResolver
    from pending_step_failure_recorder import PendingStepFailureRecorder

    active_run = ActiveRunPointerStore()
    run_locator = ActiveRunLocator(base_dir_resolver=base_dir_resolver or RunsBaseDirResolver(), active_run=active_run)
    assembly = build_default_assembly()
    resolving_flow_loader = NameResolvingFlowLoader(
        file_resolver=FlowFileResolver(path_checker=PathChecker()),
        inner_loader=assembly.flow_loader,
    )
    completion_checker = RunCompletionChecker(event_appender=assembly.event_appender, active_run=active_run)
    attempt_failure_handler = AttemptFailureHandler(
        event_appender=assembly.event_appender,
        event_replayer=assembly.event_replayer,
        completion_checker=completion_checker,
    )
    status_reader = FlowStatusReader(
        run_locator=run_locator,
        flow_loader=resolving_flow_loader,
        run_snapshot_resolver=RunSnapshotResolver(
            event_replayer=assembly.event_replayer,
            context_builder=RunContextBuilder(),
            dag_runner=assembly.dag_runner,
        ),
    )
    failure_recorder = PendingStepFailureRecorder(
        run_locator=run_locator,
        flow_loader=resolving_flow_loader,
        attempt_failure_handler=attempt_failure_handler,
    )
    return FlowTransitionGate(status_reader=status_reader, failure_recorder=failure_recorder)