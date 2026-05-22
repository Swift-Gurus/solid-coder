"""
solid-description: Wires health check components and exposes _check for the pre-write gate hook.
solid-category: service
solid-tags: [hook]
"""

import json
import sys
from pathlib import Path
from typing import Optional

_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from hook_utils import GateLogger, PLUGIN_ROOT, GATEWAY
from hc_tag_detector import TagDetector
from hc_rule_loader import GatewayRuleLoader, GatewayCommandRunner, GatewayInvoker
from hc_violation_parser import ViolationParser
from hc_checker import LLMHealthChecker, HealthPromptBuilder, PrinciplesLoader, LLMReviewer
from hc_runner_factory import make_llm_runner

SUPPORTED_EXTENSIONS: dict = {
    ".swift": "Swift",
    ".py": "Python",
}


def _check(content: str, path: str, language: str, parent_session_id: str) -> Optional[list]:
    pipeline_server = str(PLUGIN_ROOT / "mcp-server" / "pipeline" / "server.py")
    docs_server = str(PLUGIN_ROOT / "mcp-server" / "server.py")
    mcp_config = json.dumps({
        "mcpServers": {
            "pipeline": {"command": "python3", "args": [pipeline_server]},
            "docs": {"command": "python3", "args": [docs_server]},
        }
    })
    allowed_tools = (
        "mcp__pipeline__search_codebase,"
        "mcp__docs__load_fix_for_violation,"
        "mcp__docs__score_severity"
    )
    logger = GateLogger(PLUGIN_ROOT / ".claude" / "solid-coder-gate.log")
    checker = LLMHealthChecker(
        loader=PrinciplesLoader(
            rules=GatewayRuleLoader(invoker=GatewayInvoker(GATEWAY, GatewayCommandRunner())),
            tags=TagDetector(),
        ),
        builder=HealthPromptBuilder(),
        reviewer=LLMReviewer(
            runner=make_llm_runner(
                mcp_config=mcp_config, allowed_tools=allowed_tools,
                session_id=parent_session_id, file_path=path,
            ),
            logger=logger,
            parser=ViolationParser(),
        ),
    )
    return checker.check(content, path, language, parent_session_id)
