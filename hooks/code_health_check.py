"""
solid-description: Wires health check components and exposes _check for the pre-write gate hook.
solid-category: service
solid-tags: [hook]
"""

import json
import sys
from pathlib import Path
from typing import Optional

HOOKS_DIR = Path(__file__).resolve().parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

from hook_utils import GateLogger
from hc_tag_detector import TagDetector
from hc_rule_loader import GatewayRuleLoader, GatewayCommandRunner
from hc_violation_parser import ViolationParser
from hc_checker import (
    LLMHealthChecker, ClaudeRunner, HealthPromptBuilder,
    PrinciplesLoader, LLMReviewer,
)

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
GATEWAY = PLUGIN_ROOT / "mcp-server" / "gateway.py"

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
    logger = GateLogger(PLUGIN_ROOT / ".claude" / "solid-coder-gate.log")
    checker = LLMHealthChecker(
        loader=PrinciplesLoader(
            rules=GatewayRuleLoader(GATEWAY, GatewayCommandRunner()),
            tags=TagDetector(),
        ),
        builder=HealthPromptBuilder(),
        reviewer=LLMReviewer(
            runner=ClaudeRunner(
                mcp_config=mcp_config,
                allowed_tools=(
                    "mcp__pipeline__search_codebase,"
                    "mcp__docs__load_fix_for_violation,"
                    "mcp__docs__score_severity"
                ),
            ),
            logger=logger,
            parser=ViolationParser(),
        ),
    )
    return checker.check(content, path, language, parent_session_id)
