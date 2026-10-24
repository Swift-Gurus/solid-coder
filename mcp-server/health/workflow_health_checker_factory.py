"""Composes flow-based source-health checking."""

from pathlib import Path

from code_health_check_request import CodeHealthCheckRequest
from codex_flow_continuation_instruction_builder import (
    FLAT_SUBMISSION_SCAFFOLD,
    NESTED_SUBMISSION_SCAFFOLD,
    CodexFlowContinuationInstructionBuilder,
)
from flow_review_result_reader import FlowReviewResultReader
from gate_flow_prompt_builder import GateFlowPromptBuilder
from gate_logger import GateLogger
from gate_review_input_builder import GateReviewInputBuilder
from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.flow_submission_format import FlowSubmissionFormat
from harness.path_builder import PathBuilder
from harness.project_context import ProjectDirectory
from harness.runs_base_dir_resolver import RunsBaseDirResolver
from harness.sha256_content_hasher import Sha256ContentHasher
from harness.static_session_id_reader import StaticSessionIdReader
from hc_checker import HealthChecking
from health_checker_creating import HealthCheckerCreating
from health_review_assessor import HealthReviewAssessor
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
from source.analysis.operations.verify_introduced_interfaces_operation import (
    VerifyIntroducedInterfacesOperation,
)
from source.path_source_bytes_reader import PathSourceBytesReader
from source.source_analysis_operation_factory import SourceAnalysisOperationFactory
from source.source_operation_registrations_factory import (
    SourceOperationRegistrationsFactory,
)
from utils.debug_logger import DebugLogger
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
            submission_format=config.feature_flags.flow_submission_format,
            project_directory=project_directory,
            session_reader=StaticSessionIdReader(request.parent_session_id),
            session_delegate_max_workers=(config.flow_engine.max_parallel_sessions),
            operation_registrations=[
                *SourceOperationRegistrationsFactory(
                    project_directory=project_directory,
                ).make(),
                *ReviewOperationRegistrationsFactory().make(project_directory),
            ],
        ).build()
        continuation_instruction_builder = (
            CodexFlowContinuationInstructionBuilder(
                scaffold=(
                    FLAT_SUBMISSION_SCAFFOLD
                    if config.feature_flags.flow_submission_format
                    is FlowSubmissionFormat.FLAT_ARRAY
                    else NESTED_SUBMISSION_SCAFFOLD
                ),
            )
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
            assessor=HealthReviewAssessor(ScoredReviewViolationSelector()),
            introductions=VerifyIntroducedInterfacesOperation(
                reader=PathSourceBytesReader(),
                analyzer=SourceAnalysisOperationFactory().make(project_directory),
                paths=PathBuilder(),
                hasher=Sha256ContentHasher(),
            ),
            logger=GateLogger(
                DebugLogger(
                    project_dir_fn=lambda: solid_coder_project_dir(project_root),
                    filename="gate.log",
                )
            ),
            input_builder=GateReviewInputBuilder(),
            prompt_builder=GateFlowPromptBuilder(continuation_instruction_builder),
            timeout_seconds=config.llm.timeout,
        )
