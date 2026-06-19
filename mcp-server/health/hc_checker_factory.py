"""
solid-name: hc_checker_factory
solid-category: service
solid-tags: [hook]
solid-description: Provides health checker instances for code quality evaluation.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

_HEALTH_DIR = Path(__file__).resolve().parent
_HOOKS_DIR = _HEALTH_DIR.parents[1] / 'hooks'
for _d in (_HOOKS_DIR, _HEALTH_DIR, _HEALTH_DIR / 'config', _HEALTH_DIR / 'llm', _HEALTH_DIR / 'codex'):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from hook_utils import GateLogger, GATEWAY  # noqa: E402
from hc_checker import (  # noqa: E402
    HealthChecking, LLMHealthChecker, HealthPromptBuilder, PrinciplesLoader,
    LLMReviewer, LLMExecutor, FileBasedOutputHandler, FileOutputReader,
)
from output_path_resolver import OutputPathResolving, SessionOutputPathResolver  # noqa: E402
from violation_extractor import ViolationExtractor  # noqa: E402
from hc_rule_loader import GatewayRuleLoader, GatewayCommandRunner, GatewayInvoker  # noqa: E402
from hc_config import bare_session_timeout, debug_mode  # noqa: E402
from hc_runner_factory import make_llm_runner  # noqa: E402
from hc_tag_detector import TagDetector  # noqa: E402
from health_check_context_writer import HealthCheckContextWriter  # noqa: E402

_ALLOWED_TOOLS = (
    "Read,"
    "mcp__pipeline__search_codebase,"
    "mcp__pipeline__submit_batch_findings,"
    "mcp__pipeline__submit_fix,"
    "mcp__docs__load_fix_for_violation,"
    "mcp__docs__score_severity"
)


class GatewayOutputPathResolver:
    """Resolves a unique UUID-based output dir per gate invocation via the gateway CLI."""

    def __init__(self, invoker: GatewayInvoker, fallback: OutputPathResolving) -> None:
        self._invoker = invoker
        self._fallback = fallback

    def resolve(self, session_id: str) -> str:
        result = self._invoker.invoke(
            "get_output_path",
            extra_args=["--operation", "health"],
            result_key="output_root",
        )
        return result if result else self._fallback.resolve(session_id)


def make_health_checker(
    mcp_config: str,
    session_id: str = "",
    file_path: str = "",
    log_path: Optional[Path] = None,
) -> HealthChecking:
    logger = GateLogger(log_path)
    invoker = GatewayInvoker(GATEWAY, GatewayCommandRunner())
    return LLMHealthChecker(
        loader=PrinciplesLoader(
            rules=GatewayRuleLoader(invoker=invoker),
            tags=TagDetector(),
        ),
        builder=HealthPromptBuilder(),
        reviewer=LLMReviewer(
            executor=LLMExecutor(
                runner=make_llm_runner(
                    mcp_config=mcp_config,
                    allowed_tools=_ALLOWED_TOOLS,
                    session_id=session_id,
                    file_path=file_path,
                ),
                logger=logger,
                timeout=bare_session_timeout(),
            ),
            output_handler=FileBasedOutputHandler(
                FileOutputReader(
                    extractor=ViolationExtractor(),
                    debug=debug_mode(),
                )
            ),
        ),
        path_resolver=GatewayOutputPathResolver(
            invoker=invoker,
            fallback=SessionOutputPathResolver(),
        ),
        context_writer=HealthCheckContextWriter(),
    )