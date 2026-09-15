"""Composes flow-based source-health checking."""

from pathlib import Path

from code_health_check_request import CodeHealthCheckRequest
from codex_flow_continuation_instruction_builder import (
    CodexFlowContinuationInstructionBuilder,
)
from flow_review_result_reader import FlowReviewResultReader
from gate_flow_prompt_builder import GateFlowPromptBuilder
from gate_review_input_builder import GateReviewInputBuilder
from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.project_context import ProjectDirectory
from harness.runs_base_dir_resolver import RunsBaseDirResolver
from harness.static_session_id_reader import StaticSessionIdReader
from health_checker_creating import HealthCheckerCreating
from hc_checker import HealthChecking
from hook_utils import solid_coder_project_dir
from native_flow_continuation_instruction_builder import (
    NativeFlowContinuationInstructionBuilder,
)
from pipeline.flow_result_renderer_creator import FlowResultRendererCreator
from review.review_operation_registrations_factory import (
    ReviewOperationRegistrationsFactory,
)
from runner_strategy_base import RunnerStrategyBase
from scored_review_violation_selector import ScoredReviewViolationSelector
from solid_coder_config import SolidCoderConfig
from source.source_operation_registrations_factory import (
    SourceOperationRegistrationsFactory,
)
from workflow_health_checker import WorkflowHealthChecker


_ALLOWED_TOOLS = "Read,mcp__solid-coder-flow-engine__flow_next"


"""
solid-name: WorkflowHealthCheckerFactory
solid-category: factory
solid-spec: [SPEC-036, SPEC-039, SPEC-041]
solid-description: Provides request-scoped source-health workflow checking.
"""
class WorkflowHealthCheckerFactory(HealthCheckerCreating):
    def __init__(
        self,
        plugin_root: Path,
        project_root: Path,
        config: SolidCoderConfig,
        strategy: RunnerStrategyBase,
        mcp_config: str,
    ) -> None:
        self._plugin_root = plugin_root
        self._project_root = project_root
        self._config = config
        self._strategy = strategy
        self._mcp_config = mcp_config

    def make(self, request: CodeHealthCheckRequest) -> HealthChecking:
        project_root = self._project_root
        project_directory = ProjectDirectory(path=project_root)
        config = self._config
        runs = RunsBaseDirResolver(
            project_dir_fn=lambda: solid_coder_project_dir(project_root)
        )
        flow = FlowRunOrchestratorFactory(
            base_dir_resolver=runs,
            plugin_root=self._plugin_root,
            project_directory=project_directory,
            session_reader=StaticSessionIdReader(request.parent_session_id),
            session_delegate_max_workers=(
                config.flow_engine.max_parallel_sessions
            ),
            operation_registrations=[
                *SourceOperationRegistrationsFactory(
                    project_directory=project_directory,
                ).make(),
                *ReviewOperationRegistrationsFactory().make(),
            ],
        ).build()
        continuation_instruction_builder = (
            CodexFlowContinuationInstructionBuilder()
            if config.llm.backend.lower() == "codex"
            else NativeFlowContinuationInstructionBuilder()
        )
        return WorkflowHealthChecker(
            flow=flow,
            renderer=FlowResultRendererCreator().create(),
            runner=self._strategy.make_runner(
                mcp_config=self._mcp_config,
                allowed_tools=_ALLOWED_TOOLS,
                session_id=request.parent_session_id,
                file_path=request.path,
                cwd=str(project_root),
            ),
            result_reader=FlowReviewResultReader(runs),
            violation_selector=ScoredReviewViolationSelector(),
            input_builder=GateReviewInputBuilder(),
            prompt_builder=GateFlowPromptBuilder(
                continuation_instruction_builder
            ),
            timeout_seconds=config.llm.timeout,
        )
