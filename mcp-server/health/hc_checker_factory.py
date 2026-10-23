"""
solid-name: hc_checker_factory
solid-category: service
solid-tags: [hook]
solid-description: Creates health checkers that validate code.
"""

from __future__ import annotations

import sys
from pathlib import Path

from pydantic import TypeAdapter

_HEALTH_DIR = Path(__file__).resolve().parent
_MCP_DIR = _HEALTH_DIR.parent
for _d in (
    _MCP_DIR,
    _HEALTH_DIR,
    _HEALTH_DIR / "config",
    _HEALTH_DIR / "llm",
    _HEALTH_DIR / "codex",
):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from code_health_check_request import CodeHealthCheckRequest
from hc_checker import (
    FileBasedOutputHandler,
    FileOutputReader,
    HealthChecking,
    HealthPromptBuilder,
    LLMExecutor,
    LLMHealthChecker,
    LLMReviewer,
    PrinciplesLoader,
)
from hc_tag_detector import TagDetector
from health.gateway.gateway_candidate_tags_loader import GatewayCandidateTagsLoader
from health.gateway.gateway_command_runner import GatewayCommandRunner
from health.gateway.gateway_detection_rules_loader import GatewayDetectionRulesLoader
from health.gateway.gateway_rule_loader import GatewayRuleLoader
from health_check_context_writer_factory import HealthCheckContextWriterFactory
from health_checker_creating import HealthCheckerCreating
from health_output_path_resolver import HealthOutputPathResolver
from hook_utils import GATEWAY, GateLogger, solid_coder_project_dir
from legacy_health_violation_payload import LegacyHealthViolationPayload
from output_path_resolver import SessionOutputPathResolver
from runner_strategy_base import RunnerStrategyBase
from solid_coder_config import SolidCoderConfig
from typed_legacy_violation_extractor import TypedLegacyViolationExtractor
from utils.debug_logger import DebugLogger
from violation_extractor import ViolationExtractor

_ALLOWED_TOOLS = (
    "Read,"
    "mcp__pipeline__search_codebase,"
    "mcp__pipeline__submit_batch_findings,"
    "mcp__pipeline__submit_fix,"
    "mcp__docs__load_fix_for_violation,"
    "mcp__docs__score_severity"
)


"""
solid-name: LegacyHealthCheckerFactory
solid-category: factory
solid-spec: [SPEC-050]
solid-description: Provides request-scoped legacy source-health checking.
"""


class LegacyHealthCheckerFactory(HealthCheckerCreating):
    def __init__(
        self,
        project_root: Path,
        config: SolidCoderConfig,
        strategy: RunnerStrategyBase,
        mcp_config: str,
    ) -> None:
        self._project_root = project_root
        self._config = config
        self._strategy = strategy
        self._mcp_config = mcp_config

    def make(self, request: CodeHealthCheckRequest) -> HealthChecking:
        log_path = solid_coder_project_dir(self._project_root) / "gate.log"
        logger = GateLogger(
            DebugLogger(
                project_dir_fn=lambda: log_path.parent,
                filename=log_path.name,
            )
        )
        llm = self._config.llm
        invoker = GatewayCommandRunner(
            GATEWAY,
            timeout=llm.timeout,
        )
        return LLMHealthChecker(
            loader=PrinciplesLoader(
                rules=GatewayRuleLoader(
                    tags=GatewayCandidateTagsLoader(invoker),
                    detection=GatewayDetectionRulesLoader(invoker),
                ),
                tags=TagDetector(),
            ),
            builder=HealthPromptBuilder(),
            reviewer=LLMReviewer(
                executor=LLMExecutor(
                    runner=self._strategy.make_runner(
                        mcp_config=self._mcp_config,
                        allowed_tools=_ALLOWED_TOOLS,
                        session_id=request.parent_session_id,
                        file_path=request.path,
                        cwd=str(self._project_root),
                    ),
                    logger=logger,
                    timeout=llm.timeout,
                ),
                output_handler=FileBasedOutputHandler(
                    FileOutputReader(
                        extractor=TypedLegacyViolationExtractor(
                            legacy=ViolationExtractor(logger=logger),
                            adapter=TypeAdapter(list[LegacyHealthViolationPayload]),
                        ),
                        debug=llm.debug,
                    )
                ),
            ),
            path_resolver=HealthOutputPathResolver(
                invoker=invoker,
                fallback=SessionOutputPathResolver(),
            ),
            context_writer=HealthCheckContextWriterFactory().make(),
        )
