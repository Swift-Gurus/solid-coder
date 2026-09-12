"""Composes flow-based source-health checking."""

from pathlib import Path
from typing import Callable

from codex_flow_continuation_instruction_builder import (
    CodexFlowContinuationInstructionBuilder,
)
from flow_review_result_reader import FlowReviewResultReader
from gate_flow_prompt_builder import GateFlowPromptBuilder
from gate_review_input_builder import GateReviewInputBuilder
from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.runs_base_dir_resolver import RunsBaseDirResolver
from harness.static_session_id_reader import StaticSessionIdReader
from hc_checker import HealthChecking
from hc_config_schema import load_config
from hc_runner_factory import make_llm_runner
from hook_utils import _resolve_project_root, solid_coder_project_dir
from native_flow_continuation_instruction_builder import (
    NativeFlowContinuationInstructionBuilder,
)
from pipeline.flow_result_renderer_creator import FlowResultRendererCreator
from review.review_operation_registrations_factory import (
    ReviewOperationRegistrationsFactory,
)
from scored_review_violation_selector import ScoredReviewViolationSelector
from solid_coder_config import SolidCoderConfig
from source.source_operation_registrations_factory import (
    SourceOperationRegistrationsFactory,
)
from workflow_health_checker import WorkflowHealthChecker


ConfigLoading = Callable[[Path], SolidCoderConfig]
_ALLOWED_TOOLS = "Read,mcp__solid-coder-flow-engine__flow_next"


"""
solid-name: WorkflowHealthCheckerFactory
solid-category: factory
solid-spec: [SPEC-036, SPEC-039, SPEC-041]
solid-description: Composes prospective source-health workflow execution for one project context.
"""
class WorkflowHealthCheckerFactory:
    def __init__(
        self,
        plugin_root: Path,
        config_loader: ConfigLoading = load_config,
    ) -> None:
        self._plugin_root = plugin_root
        self._config_loader = config_loader

    def make(
        self,
        mcp_config: str,
        session_id: str = "",
        file_path: str = "",
        cwd: str = "",
    ) -> HealthChecking:
        project_root = Path(cwd).resolve() if cwd else _resolve_project_root()
        config = self._config_loader(project_root)
        runs = RunsBaseDirResolver(
            project_dir_fn=lambda: solid_coder_project_dir(project_root)
        )
        flow = FlowRunOrchestratorFactory(
            base_dir_resolver=runs,
            plugin_root=self._plugin_root,
            project_directory=lambda: project_root,
            session_reader=StaticSessionIdReader(session_id),
            session_delegate_max_workers=(
                config.flow_engine.max_parallel_sessions
            ),
            operation_registrations=[
                *SourceOperationRegistrationsFactory(
                    project_directory=lambda: project_root,
                ).make(),
                *ReviewOperationRegistrationsFactory().make(),
            ],
        ).build()
        continuation_instruction = (
            CodexFlowContinuationInstructionBuilder().build
            if config.llm.backend.lower() == "codex"
            else NativeFlowContinuationInstructionBuilder().build
        )
        return WorkflowHealthChecker(
            flow=flow,
            renderer=FlowResultRendererCreator().create(),
            runner=make_llm_runner(
                mcp_config=mcp_config,
                allowed_tools=_ALLOWED_TOOLS,
                session_id=session_id,
                file_path=file_path,
                cwd=str(project_root),
            ),
            result_reader=FlowReviewResultReader(runs),
            violation_selector=ScoredReviewViolationSelector(),
            input_builder=GateReviewInputBuilder(),
            prompt_builder=GateFlowPromptBuilder(continuation_instruction),
            timeout_seconds=config.llm.timeout,
        )
