"""
solid-name: FlowTransitionGateFactory
solid-category: service
solid-spec: [SPEC-032]
solid-description: Creates instances with all dependencies configured.
solid-tags: [hook]
"""

from __future__ import annotations

import sys
from pathlib import Path

_MCP_DIR = Path(__file__).resolve().parents[1]
if str(_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(_MCP_DIR))

from flow_transition_evaluating import FlowTransitionGate  # noqa: E402


"""
solid-name: FlowTransitionGateFactory
solid-category: service
solid-spec: [SPEC-032]
solid-description: Provides a ready-to-use flow-transition decision service.
solid-tags: [hook]
"""
class FlowTransitionGateFactory:
    """Factory: wires a FlowTransitionGate against the real filesystem, using production defaults.

    OCP Factory exception: constructing, holding, and wiring concrete dependencies
    is inherently this class's job.
    """

    def __init__(self, base_dir_resolver=None, session_id: str = "") -> None:
        self._base_dir_resolver = base_dir_resolver
        self._session_id = session_id

    def build(self) -> FlowTransitionGate:
        from harness.active_run_locator import ActiveRunLocator
        from harness.active_run_pointer_store import ActiveRunPointerStore
        from harness.attempt_exhaustion_evaluator import AttemptExhaustionEvaluator
        from harness.attempt_exhaustion_message_builder import AttemptExhaustionMessageBuilder
        from harness.attempt_failure_handler import AttemptFailureHandler
        from harness.flow_engine_assembly_factory import FlowEngineAssemblyFactory
        from harness.flow_file_resolver import FlowFileResolver
        from harness.flow_status_reader import FlowStatusReader
        from harness.name_resolving_flow_loader import NameResolvingFlowLoader
        from harness.path_checking import PathChecker
        from harness.run_completion_checker import RunCompletionChecker
        from harness.run_context_builder import RunContextBuilder
        from harness.run_snapshot_resolver import RunSnapshotResolver
        from harness.run_timeout_message_builder import RunTimeoutMessageBuilder
        from harness.runs_base_dir_resolver import RunsBaseDirResolver
        from harness.session_scoped_active_path_resolver import SessionScopedActivePathResolver
        from harness.static_session_id_reader import StaticSessionIdReader
        from harness.workflow_catalog_factory import make_workflow_catalog_resolver
        from pending_step_failure_recorder import PendingStepFailureRecorder

        active_run = ActiveRunPointerStore(
            path_resolver=SessionScopedActivePathResolver(session_id_reader=StaticSessionIdReader(self._session_id))
        )
        run_locator = ActiveRunLocator(
            base_dir_resolver=self._base_dir_resolver or RunsBaseDirResolver(), active_run=active_run
        )
        workflow_catalog = make_workflow_catalog_resolver()
        assembly = FlowEngineAssemblyFactory().build(
            workflow_catalog_resolver=workflow_catalog,
        )
        resolving_flow_loader = NameResolvingFlowLoader(
            file_resolver=FlowFileResolver(
                path_checker=PathChecker(),
                catalog_resolver=workflow_catalog,
            ),
            inner_loader=assembly.flow_loader,
            catalog_scope=workflow_catalog,
        )
        completion_checker = RunCompletionChecker(
            event_appender=assembly.event_appender,
            active_run=active_run,
            exhaustion_evaluator=AttemptExhaustionEvaluator(),
            exhaustion_message_builder=AttemptExhaustionMessageBuilder(),
            timeout_message_builder=RunTimeoutMessageBuilder(),
        )
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
