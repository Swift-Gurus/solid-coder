"""
solid-name: hc_checker_factory
solid-category: service
solid-tags: [hook]
solid-description: Creates a health checker configured to evaluate source code against quality principles.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from hook_utils import GateLogger, PLUGIN_ROOT, GATEWAY  # noqa: E402
from hc_checker import (  # noqa: E402
    HealthChecking, LLMHealthChecker, HealthPromptBuilder, PrinciplesLoader,
    LLMReviewer, LLMExecutor, FileBasedOutputHandler, FileOutputReader,
)
from hc_rule_loader import GatewayRuleLoader, GatewayCommandRunner, GatewayInvoker  # noqa: E402
from hc_config import bare_session_timeout, debug_mode  # noqa: E402
from hc_runner_factory import make_llm_runner  # noqa: E402
from hc_tag_detector import TagDetector  # noqa: E402

_ALLOWED_TOOLS = (
    "Read,"
    "mcp__pipeline__search_codebase,"
    "mcp__pipeline__submit_batch_findings,"
    "mcp__pipeline__submit_fix,"
    "mcp__docs__load_fix_for_violation,"
    "mcp__docs__score_severity"
)


def make_health_checker(
    mcp_config: str,
    session_id: str = "",
    file_path: str = "",
    log_path: Optional[Path] = None,
) -> HealthChecking:
    logger = GateLogger(log_path or PLUGIN_ROOT / ".claude" / "solid-coder-gate.log")
    return LLMHealthChecker(
        loader=PrinciplesLoader(
            rules=GatewayRuleLoader(invoker=GatewayInvoker(GATEWAY, GatewayCommandRunner())),
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
            output_handler=FileBasedOutputHandler(FileOutputReader(_debug=debug_mode())),
        ),
    )
