"""Composes flow-run orchestration dependencies."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from harness.active_run_locator import ActiveRunLocator
from harness.active_run_location_assembler import ActiveRunLocationAssembler
from harness.active_run_lock_clearer import ActiveRunLockClearer
from harness.active_run_pointer_store import ActiveRunPointerStore
from harness.agent_step_handler import AgentStepHandler
from harness.attempt_exhaustion_evaluator import AttemptExhaustionEvaluator
from harness.attempt_exhaustion_message_builder import AttemptExhaustionMessageBuilder
from harness.attempt_failure_handler import AttemptFailureHandler
from harness.command_allowlist_resolving import CommandAllowlistResolving
from harness.concurrent_session_delegate_batch_runner import ConcurrentSessionDelegateBatchRunner
from harness.condition_serializer_factory import make_condition_serializer
from harness.delegate_instruction_builder import DelegateInstructionBuilder
from harness.delegate_step_handler import DelegateStepHandler
from harness.engine_step_drainer import EngineStepDrainer
from harness.executor_item_mapper import ExecutorItemMapper
from harness.existing_path_filter import ExistingPathFilter
from harness.execution_and_readiness_coordinator import ExecutionAndReadinessCoordinator
from harness.flow_engine_assembly_factory import FlowEngineAssemblyFactory
from harness.flow_file_resolver import FlowFileResolver
from harness.flow_initializer import FlowInitializer
from harness.flow_run_orchestrator import FlowRunOrchestrator
from harness.flow_search_path_resolver import FlowSearchPathResolver
from harness.flow_start_result_builder import FlowStartResultBuilder
from harness.flow_starter import FlowStarter
from harness.flow_status_reader import FlowStatusReader
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.flow_stepper import FlowStepper
from harness.interpolation_guard import InterpolationGuard
from harness.isolated_run_path_resolver import IsolatedRunPathResolver
from harness.json_loading import JsonLoader
from harness.logical_operation_name_validator import LogicalOperationNameValidator
from harness.name_resolving_flow_loader import NameResolvingFlowLoader
from harness.operation_registration import OperationRegistration
from harness.operation_registry import OperationRegistry
from harness.operation_step_executor import OperationStepExecutor
from harness.operation_step_runner_adapter import OperationStepRunnerAdapter
from harness.output_recorder import OutputRecorder
from harness.output_submission_advancer import OutputSubmissionAdvancer
from harness.pass_through_step_submission_validator import PassThroughStepSubmissionValidator
from harness.path_checking import PathChecker
from harness.plugin_workflow_search_path_resolver import PluginWorkflowSearchPathResolver
from harness.project_workflow_search_path_resolver import ProjectWorkflowSearchPathResolver
from harness.ready_step_executor import ReadyStepExecutor
from harness.process_execution_factory import ProcessExecutionFactory
from harness.process_execution_runner_adapter import ProcessExecutionRunnerAdapter
from harness.process_step_executor import ProcessStepExecutor
from harness.process_step_handler import ProcessStepHandler
from harness.pydantic_operation_invoker import PydanticOperationInvoker
from harness.run_completion_checker import RunCompletionChecker
from harness.run_context_builder import RunContextBuilder
from harness.run_directory_scaffolder import RunDirectoryScaffolder
from harness.run_initializer import RunInitializer
from harness.run_metadata_store import RunMetadataStore
from harness.run_provisioner import RunProvisioner
from harness.rule_run_finalizer_factory import RuleRunFinalizerFactory
from harness.run_snapshot_resolver import RunSnapshotResolver
from harness.run_started_event_recorder import RunStartedEventRecorder
from harness.run_timeout_message_builder import RunTimeoutMessageBuilder
from harness.runs_base_dir_resolving import RunsBaseDirResolving
from harness.safe_session_delegate_instance_runner import SafeSessionDelegateInstanceRunner
from harness.script_failure_attributor import ScriptFailureAttributor
from harness.script_outcome_evaluator import ScriptOutcomeEvaluator
from harness.session_delegate_runner import SessionDelegateRunner
from harness.session_delegate_running import SessionDelegateRunning
from harness.session_delegate_step_batch_runner import SessionDelegateStepBatchRunner
from harness.session_id_reading import SessionIdReading
from harness.session_scoped_active_path_resolver import SessionScopedActivePathResolver
from harness.static_session_id_reader import StaticSessionIdReader
from harness.startup_context_resolver import StartupContextResolver
from harness.step_execution_failure_handler import StepExecutionFailureHandler
from harness.step_execution_batch_advancer import StepExecutionBatchAdvancer
from harness.step_batch_runner_registration import StepBatchRunnerRegistration
from harness.step_batch_runner_resolver import StepBatchRunnerResolver
from harness.step_handler_resolver import StepHandlerResolver
from harness.step_process_execution_resolver import StepProcessExecutionResolver
from harness.step_output_validator import StepOutputValidator
from harness.step_output_shape_checker import StepOutputShapeChecker
from harness.step_output_submission_collector import StepOutputSubmissionCollector
from harness.step_result_builder import StepResultBuilder
from harness.step_skip_recorder import StepSkipRecorder
from harness.single_instance_step_batch_runner import SingleInstanceStepBatchRunner
from harness.successful_validation_result_provider import SuccessfulValidationResultProvider
from harness.turn_advancer import TurnAdvancer
from harness.thread_pool_executor_factory import ThreadPoolExecutorFactory
from harness.workflow_catalog_factory import make_workflow_catalog_resolver
from harness.workflow_context_values_mapper import WorkflowContextValuesMapper
from harness.workflow_condition_gate import WorkflowConditionGate
from harness.workflow_condition_recorder import WorkflowConditionRecorder
from harness.workflow_persister_factory import make_workflow_persister
from hook_utils import _resolve_project_root
from subprocess_adapter import SubprocessAdapter

_DELEGATE_SESSION_TIMEOUT_SECONDS = 300
_DELEGATE_SESSION_MAX_WORKERS = 4


"""
solid-name: FlowRunOrchestratorFactory
solid-category: service
solid-spec: [SPEC-027]
solid-description: Prepares flow-run orchestration for workflow execution.
"""
class FlowRunOrchestratorFactory:

    def __init__(
        self,
        base_dir_resolver: RunsBaseDirResolving,
        plugin_root: Path,
        command_allowlist_resolver: Optional[CommandAllowlistResolving] = None,
        session_reader: Optional[SessionIdReading] = None,
        session_delegate_runner: Optional[SessionDelegateRunning] = None,
        session_delegate_max_workers: int = _DELEGATE_SESSION_MAX_WORKERS,
        operation_registrations: Optional[list[OperationRegistration]] = None,
    ) -> None:
        self._base_dir_resolver = base_dir_resolver
        self._plugin_root = plugin_root
        self._command_allowlist_resolver = command_allowlist_resolver
        self._session_reader: SessionIdReading = session_reader or StaticSessionIdReader()
        self._session_delegate_runner = session_delegate_runner
        self._session_delegate_max_workers = session_delegate_max_workers
        self._operation_registrations = operation_registrations or []

    def build(self) -> FlowRunOrchestrator:
        workflow_catalog = make_workflow_catalog_resolver()
        path_checker = PathChecker()
        error_factory = FlowValidationErrorFactory()
        operation_registry = OperationRegistry(
            registrations=self._operation_registrations,
            name_validator=LogicalOperationNameValidator(),
            error_factory=error_factory,
        )
        assembly = FlowEngineAssemblyFactory().build(
            command_allowlist_resolver=self._command_allowlist_resolver,
            workflow_catalog_resolver=workflow_catalog,
            operation_registry=operation_registry,
        )
        active_run = ActiveRunPointerStore(
            path_resolver=SessionScopedActivePathResolver(session_id_reader=self._session_reader)
        )
        metadata_store = RunMetadataStore()
        step_result_builder = StepResultBuilder()
        run_locator = ActiveRunLocator(base_dir_resolver=self._base_dir_resolver, active_run=active_run)
        resolving_flow_loader = NameResolvingFlowLoader(
            file_resolver=FlowFileResolver(
                path_checker=path_checker,
                catalog_resolver=workflow_catalog,
            ),
            inner_loader=assembly.flow_loader,
            catalog_scope=workflow_catalog,
        )
        run_context_builder = RunContextBuilder(
            values_mapper=WorkflowContextValuesMapper()
        )
        run_snapshot_resolver = RunSnapshotResolver(
            event_replayer=assembly.event_replayer,
            context_builder=run_context_builder,
            step_resolver=assembly.dynamic_step_resolver,
            dag_runner=assembly.dag_runner,
        )
        output_recorder = OutputRecorder(event_appender=assembly.event_appender)
        completion_checker = RunCompletionChecker(
            event_appender=assembly.event_appender,
            active_run=active_run,
            exhaustion_evaluator=AttemptExhaustionEvaluator(),
            exhaustion_message_builder=AttemptExhaustionMessageBuilder(),
            timeout_message_builder=RunTimeoutMessageBuilder(),
            finalizer=RuleRunFinalizerFactory().build(assembly.event_appender),
        )
        attempt_failure_handler = AttemptFailureHandler(
            event_appender=assembly.event_appender,
            event_replayer=assembly.event_replayer,
            completion_checker=completion_checker,
        )
        agent_handler = AgentStepHandler(
            output_validator=StepOutputValidator(
                schema_validator=assembly.schema_validator,
                shape_checker=StepOutputShapeChecker(),
                submission_collector=StepOutputSubmissionCollector(),
            )
        )
        process_handler = ProcessStepHandler(
            executor=ProcessStepExecutor(
                execution_resolver=StepProcessExecutionResolver(
                    ProcessExecutionFactory(FlowValidationErrorFactory())
                ),
                runner=ProcessExecutionRunnerAdapter(SubprocessAdapter()),
                evaluator=ScriptOutcomeEvaluator(schema_validator=assembly.schema_validator),
            ),
            submission_validator=PassThroughStepSubmissionValidator(
                SuccessfulValidationResultProvider()
            ),
        )
        operation_handler = ProcessStepHandler(
            executor=OperationStepRunnerAdapter(
                OperationStepExecutor(
                    registry=operation_registry,
                    invoker=PydanticOperationInvoker(error_factory),
                    error_factory=error_factory,
                )
            ),
            submission_validator=PassThroughStepSubmissionValidator(
                SuccessfulValidationResultProvider()
            ),
        )
        session_delegate_runner = self._session_delegate_runner or SessionDelegateRunner(
            plugin_root=self._plugin_root,
            timeout=_DELEGATE_SESSION_TIMEOUT_SECONDS,
            output_loader=JsonLoader(),
        )
        delegate_handler = DelegateStepHandler(
            agent_handler=agent_handler,
            session_runner=session_delegate_runner,
        )
        step_handler_resolver = StepHandlerResolver(handlers={
            "agent": agent_handler,
            "metric": agent_handler,
            "exception": agent_handler,
            "script": process_handler,
            "command": process_handler,
            "delegate": delegate_handler,
            "operation": operation_handler,
        })
        single_agent_batch = SingleInstanceStepBatchRunner(agent_handler)
        single_process_batch = SingleInstanceStepBatchRunner(process_handler)
        single_delegate_batch = SingleInstanceStepBatchRunner(delegate_handler)
        single_operation_batch = SingleInstanceStepBatchRunner(operation_handler)
        session_delegate_batch = SessionDelegateStepBatchRunner(
            ConcurrentSessionDelegateBatchRunner(
                item_mapper=ExecutorItemMapper(ThreadPoolExecutorFactory()),
                instance_runner=SafeSessionDelegateInstanceRunner(
                    runner=session_delegate_runner,
                    instruction_builder=DelegateInstructionBuilder(),
                ),
                max_workers=self._session_delegate_max_workers,
            )
        )
        batch_runner_resolver = StepBatchRunnerResolver(registrations=[
            StepBatchRunnerRegistration("delegate", "session", session_delegate_batch),
            StepBatchRunnerRegistration("delegate", "subagent", single_delegate_batch),
            StepBatchRunnerRegistration("agent", "", single_agent_batch),
            StepBatchRunnerRegistration("metric", "", single_agent_batch),
            StepBatchRunnerRegistration("exception", "", single_agent_batch),
            StepBatchRunnerRegistration("script", "", single_process_batch),
            StepBatchRunnerRegistration("command", "", single_process_batch),
            StepBatchRunnerRegistration("operation", "", single_operation_batch),
        ])
        condition_serializer = make_condition_serializer()
        step_execution_failure_handler = StepExecutionFailureHandler(
            failure_attributor=ScriptFailureAttributor(),
            attempt_failure_handler=attempt_failure_handler,
        )
        step_execution_coordinator = EngineStepDrainer(
            run_snapshot_resolver=run_snapshot_resolver,
            workflow_condition_gate=WorkflowConditionGate(
                context_builder=run_context_builder,
                condition_evaluator=assembly.condition_evaluator,
                decision_recorder=WorkflowConditionRecorder(
                    event_appender=assembly.event_appender,
                    condition_serializer=condition_serializer,
                ),
            ),
            step_skip_recorder=StepSkipRecorder(
                event_appender=assembly.event_appender,
                condition_serializer=condition_serializer,
            ),
            ready_step_executor=ReadyStepExecutor(
                batch_runner_resolver=batch_runner_resolver,
                batch_advancer=StepExecutionBatchAdvancer(
                    validator_resolver=step_handler_resolver,
                    output_recorder=output_recorder,
                    failure_handler=step_execution_failure_handler,
                ),
                output_recorder=output_recorder,
            ),
        )
        interpolation_guard = InterpolationGuard()
        execution_and_readiness_coordinator = ExecutionAndReadinessCoordinator(
            step_execution_coordinator=step_execution_coordinator,
            step_result_builder=step_result_builder,
            interpolation_guard=interpolation_guard,
            run_snapshot_resolver=run_snapshot_resolver,
            completion_checker=completion_checker,
        )
        flow_initializer = FlowInitializer(
            startup_context=StartupContextResolver(
                base_dir_resolver=self._base_dir_resolver,
                search_paths=FlowSearchPathResolver(
                    sources=[
                        ProjectWorkflowSearchPathResolver(_resolve_project_root),
                        PluginWorkflowSearchPathResolver(self._plugin_root),
                    ],
                    path_filter=ExistingPathFilter(path_checker),
                ),
            ),
            flow_loader=resolving_flow_loader,
            run_provisioner=RunProvisioner(
                run_initializer=RunInitializer(
                    active_run=active_run,
                    scaffolder=RunDirectoryScaffolder(
                        workflow_persister=make_workflow_persister(),
                    ),
                ),
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
            execution_and_readiness_coordinator=execution_and_readiness_coordinator,
            interpolation_guard=interpolation_guard,
        )
        status_reader = FlowStatusReader(
            run_locator=run_locator,
            flow_loader=resolving_flow_loader,
            run_snapshot_resolver=run_snapshot_resolver,
            condition_serializer=condition_serializer,
        )
        lock_clearer = ActiveRunLockClearer(run_locator=run_locator, active_run=active_run)

        return FlowRunOrchestrator(
            starter=starter, stepper=stepper, status_reader=status_reader, lock_clearer=lock_clearer
        )
