"""
solid-name: FlowRunOrchestratorFactory
solid-category: service
solid-spec: [SPEC-027]
solid-description: Creates orchestrators for executing flows.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from harness.active_run_locator import ActiveRunLocator
from harness.active_run_location_assembler import ActiveRunLocationAssembler
from harness.active_run_lock_clearer import ActiveRunLockClearer
from harness.active_run_pointer_store import ActiveRunPointerStore
from harness.agent_step_handler import AgentStepHandler
from harness.attempt_failure_handler import AttemptFailureHandler
from harness.command_allowlist_resolving import CommandAllowlistResolving
from harness.delegate_step_handler import DelegateStepHandler
from harness.execution_and_readiness_coordinator import ExecutionAndReadinessCoordinator
from harness.flow_engine_assembly import build_default_assembly
from harness.flow_file_resolver import FlowFileResolver
from harness.flow_initializer import FlowInitializer
from harness.flow_run_orchestrator import FlowRunOrchestrator
from harness.flow_search_path_resolver import FlowSearchPathResolver
from harness.flow_start_result_builder import FlowStartResultBuilder
from harness.flow_starter import FlowStarter
from harness.flow_status_reader import FlowStatusReader
from harness.flow_stepper import FlowStepper
from harness.interpolation_guard import InterpolationGuard
from harness.isolated_run_path_resolver import IsolatedRunPathResolver
from harness.name_resolving_flow_loader import NameResolvingFlowLoader
from harness.output_recorder import OutputRecorder
from harness.output_submission_advancer import OutputSubmissionAdvancer
from harness.path_checking import PathChecker
from harness.ready_steps_resolver import ReadyStepsResolver
from harness.run_completion_checker import RunCompletionChecker
from harness.run_context_builder import RunContextBuilder
from harness.run_directory_scaffolder import RunDirectoryScaffolder
from harness.run_initializer import RunInitializer
from harness.run_metadata_store import RunMetadataStore
from harness.run_provisioner import RunProvisioner
from harness.run_snapshot_resolver import RunSnapshotResolver
from harness.run_started_event_recorder import RunStartedEventRecorder
from harness.runs_base_dir_resolving import RunsBaseDirResolving
from harness.script_failure_attributor import ScriptFailureAttributor
from harness.script_outcome_evaluator import ScriptOutcomeEvaluator
from harness.script_step_handler import ScriptStepHandler
from harness.session_delegate_runner import SessionDelegateRunner
from harness.session_id_reading import SessionIdReading
from harness.session_scoped_active_path_resolver import SessionScopedActivePathResolver
from harness.static_session_id_reader import StaticSessionIdReader
from harness.startup_context_resolver import StartupContextResolver
from harness.step_execution_coordinator import StepExecutionCoordinator
from harness.step_handler_resolver import StepHandlerResolver
from harness.step_output_validator import StepOutputValidator
from harness.step_result_builder import StepResultBuilder
from harness.turn_advancer import TurnAdvancer
from subprocess_script_runner import SubprocessScriptRunner

_DELEGATE_SESSION_TIMEOUT_SECONDS = 300


class FlowRunOrchestratorFactory:

    def __init__(
        self,
        base_dir_resolver: RunsBaseDirResolving,
        plugin_root: Path,
        command_allowlist_resolver: Optional[CommandAllowlistResolving] = None,
        session_reader: Optional[SessionIdReading] = None,
    ) -> None:
        self._base_dir_resolver = base_dir_resolver
        self._plugin_root = plugin_root
        self._command_allowlist_resolver = command_allowlist_resolver
        self._session_reader: SessionIdReading = session_reader or StaticSessionIdReader()

    def build(self) -> FlowRunOrchestrator:
        assembly = build_default_assembly(command_allowlist_resolver=self._command_allowlist_resolver)
        active_run = ActiveRunPointerStore(
            path_resolver=SessionScopedActivePathResolver(session_id_reader=self._session_reader)
        )
        metadata_store = RunMetadataStore()
        step_result_builder = StepResultBuilder()
        run_locator = ActiveRunLocator(base_dir_resolver=self._base_dir_resolver, active_run=active_run)
        resolving_flow_loader = NameResolvingFlowLoader(
            file_resolver=FlowFileResolver(path_checker=PathChecker()),
            inner_loader=assembly.flow_loader,
        )
        run_snapshot_resolver = RunSnapshotResolver(
            event_replayer=assembly.event_replayer,
            context_builder=RunContextBuilder(),
            dag_runner=assembly.dag_runner,
        )
        ready_steps_resolver = ReadyStepsResolver(
            run_snapshot_resolver=run_snapshot_resolver,
            step_result_builder=step_result_builder,
        )
        output_recorder = OutputRecorder(event_appender=assembly.event_appender)
        completion_checker = RunCompletionChecker(event_appender=assembly.event_appender, active_run=active_run)
        attempt_failure_handler = AttemptFailureHandler(
            event_appender=assembly.event_appender,
            event_replayer=assembly.event_replayer,
            completion_checker=completion_checker,
        )
        agent_handler = AgentStepHandler(output_validator=StepOutputValidator(schema_validator=assembly.schema_validator))
        step_handler_resolver = StepHandlerResolver(handlers={
            "agent": agent_handler,
            "script": ScriptStepHandler(
                runner=SubprocessScriptRunner(),
                evaluator=ScriptOutcomeEvaluator(schema_validator=assembly.schema_validator),
            ),
            "delegate": DelegateStepHandler(
                agent_handler=agent_handler,
                session_runner=SessionDelegateRunner(
                    plugin_root=self._plugin_root,
                    timeout=_DELEGATE_SESSION_TIMEOUT_SECONDS,
                ),
            ),
        })
        step_execution_coordinator = StepExecutionCoordinator(
            run_snapshot_resolver=run_snapshot_resolver,
            step_handler_resolver=step_handler_resolver,
            failure_attributor=ScriptFailureAttributor(),
            attempt_failure_handler=attempt_failure_handler,
            output_recorder=output_recorder,
        )
        interpolation_guard = InterpolationGuard()
        execution_and_readiness_coordinator = ExecutionAndReadinessCoordinator(
            step_execution_coordinator=step_execution_coordinator,
            ready_steps_resolver=ready_steps_resolver,
            interpolation_guard=interpolation_guard,
        )
        flow_initializer = FlowInitializer(
            startup_context=StartupContextResolver(
                base_dir_resolver=self._base_dir_resolver,
                search_paths=FlowSearchPathResolver(),
            ),
            flow_loader=resolving_flow_loader,
            run_provisioner=RunProvisioner(
                run_initializer=RunInitializer(active_run=active_run, scaffolder=RunDirectoryScaffolder()),
                metadata_store=metadata_store,
            ),
            path_resolver=IsolatedRunPathResolver(),
            location_assembler=ActiveRunLocationAssembler(),
            event_recorder=RunStartedEventRecorder(event_appender=assembly.event_appender),
        )
        starter = FlowStarter(
            initializer=flow_initializer,
            execution_and_readiness_coordinator=execution_and_readiness_coordinator,
            result_builder=FlowStartResultBuilder(),
        )
        stepper = FlowStepper(
            run_locator=run_locator,
            metadata_store=metadata_store,
            flow_loader=resolving_flow_loader,
            run_snapshot_resolver=run_snapshot_resolver,
            submission_advancer=OutputSubmissionAdvancer(
                step_handler_resolver=step_handler_resolver,
                attempt_failure_handler=attempt_failure_handler,
                session_reader=self._session_reader,
                output_recorder=output_recorder,
                turn_advancer=TurnAdvancer(event_replayer=assembly.event_replayer, event_appender=assembly.event_appender),
            ),
            completion_checker=completion_checker,
            execution_and_readiness_coordinator=execution_and_readiness_coordinator,
            interpolation_guard=interpolation_guard,
        )
        status_reader = FlowStatusReader(
            run_locator=run_locator,
            flow_loader=resolving_flow_loader,
            run_snapshot_resolver=run_snapshot_resolver,
        )
        lock_clearer = ActiveRunLockClearer(run_locator=run_locator, active_run=active_run)

        return FlowRunOrchestrator(
            starter=starter, stepper=stepper, status_reader=status_reader, lock_clearer=lock_clearer
        )
