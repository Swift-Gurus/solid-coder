"""
solid-name: FlowRunOrchestratorFactory
solid-category: service
solid-spec: [SPEC-027]
solid-description: Factory for creating fully-configured flow orchestrator instances.
"""

from __future__ import annotations

from typing import Optional

from harness.active_run_locator import ActiveRunLocator
from harness.active_run_pointer_store import ActiveRunPointerStore
from harness.agent_step_handler import AgentStepHandler
from harness.attempt_failure_handler import AttemptFailureHandler
from harness.claude_agent_type_env_detector import ClaudeAgentTypeEnvDetector
from harness.command_allowlist_resolving import CommandAllowlistResolving
from harness.execution_intent_resolver import ExecutionIntentResolver
from harness.flow_engine_assembly import build_default_assembly
from harness.flow_file_resolver import FlowFileResolver
from harness.flow_run_orchestrator import FlowRunOrchestrator
from harness.flow_search_path_resolver import FlowSearchPathResolver
from harness.flow_starter import FlowStarter
from harness.flow_status_reader import FlowStatusReader
from harness.flow_stepper import FlowStepper
from harness.mcp_request_context_session_reader import McpRequestContextSessionReader
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
from harness.runs_base_dir_resolver import RunsBaseDirResolving
from harness.script_failure_attributor import ScriptFailureAttributor
from harness.script_outcome_evaluator import ScriptOutcomeEvaluator
from harness.script_step_handler import ScriptStepHandler
from harness.startup_context_resolver import StartupContextResolver
from harness.step_execution_coordinator import StepExecutionCoordinator
from harness.step_handler_resolver import StepHandlerResolver
from harness.step_output_validator import StepOutputValidator
from harness.step_result_builder import StepResultBuilder
from harness.turn_advancer import TurnAdvancer
from subprocess_script_runner import SubprocessScriptRunner


class FlowRunOrchestratorFactory:

    def __init__(
        self,
        base_dir_resolver: RunsBaseDirResolving,
        command_allowlist_resolver: Optional[CommandAllowlistResolving] = None,
    ) -> None:
        self._base_dir_resolver = base_dir_resolver
        self._command_allowlist_resolver = command_allowlist_resolver

    def build(self) -> FlowRunOrchestrator:
        assembly = build_default_assembly(command_allowlist_resolver=self._command_allowlist_resolver)
        active_run = ActiveRunPointerStore()
        metadata_store = RunMetadataStore()
        step_result_builder = StepResultBuilder(intent_resolver=ExecutionIntentResolver())
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
        step_handler_resolver = StepHandlerResolver(handlers={
            "agent": AgentStepHandler(output_validator=StepOutputValidator(schema_validator=assembly.schema_validator)),
            "script": ScriptStepHandler(
                runner=SubprocessScriptRunner(),
                evaluator=ScriptOutcomeEvaluator(schema_validator=assembly.schema_validator),
            ),
        })
        step_execution_coordinator = StepExecutionCoordinator(
            run_snapshot_resolver=run_snapshot_resolver,
            step_handler_resolver=step_handler_resolver,
            failure_attributor=ScriptFailureAttributor(),
            attempt_failure_handler=attempt_failure_handler,
            output_recorder=output_recorder,
        )
        starter = FlowStarter(
            startup_context=StartupContextResolver(
                env_detector=ClaudeAgentTypeEnvDetector(),
                base_dir_resolver=self._base_dir_resolver,
                search_paths=FlowSearchPathResolver(),
            ),
            flow_loader=resolving_flow_loader,
            run_provisioner=RunProvisioner(
                run_initializer=RunInitializer(active_run=active_run, scaffolder=RunDirectoryScaffolder()),
                metadata_store=metadata_store,
            ),
            event_appender=assembly.event_appender,
            run_snapshot_resolver=run_snapshot_resolver,
            step_result_builder=step_result_builder,
            step_execution_coordinator=step_execution_coordinator,
        )
        stepper = FlowStepper(
            run_locator=run_locator,
            metadata_store=metadata_store,
            flow_loader=resolving_flow_loader,
            run_snapshot_resolver=run_snapshot_resolver,
            submission_advancer=OutputSubmissionAdvancer(
                step_handler_resolver=step_handler_resolver,
                attempt_failure_handler=attempt_failure_handler,
                session_reader=McpRequestContextSessionReader(),
                output_recorder=output_recorder,
                turn_advancer=TurnAdvancer(event_replayer=assembly.event_replayer, event_appender=assembly.event_appender),
            ),
            completion_checker=completion_checker,
            step_execution_coordinator=step_execution_coordinator,
            ready_steps_resolver=ready_steps_resolver,
        )
        status_reader = FlowStatusReader(
            run_locator=run_locator,
            flow_loader=resolving_flow_loader,
            run_snapshot_resolver=run_snapshot_resolver,
        )

        return FlowRunOrchestrator(starter=starter, stepper=stepper, status_reader=status_reader)
