"""
solid-name: SessionDelegateRunner
solid-category: service
solid-spec: [SPEC-027]
solid-description: Executes a provided prompt in a dedicated execution context.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

_MCP_DIR = Path(__file__).resolve().parents[1]
_HEALTH_DIR = _MCP_DIR / "health"
for _d in (
    _MCP_DIR,
    _MCP_DIR / "gate",
    _MCP_DIR / "patch",
    _MCP_DIR / "output",
    _MCP_DIR / "utils",
    _MCP_DIR / "session",
    _HEALTH_DIR,
    _HEALTH_DIR / "config",
    _HEALTH_DIR / "llm",
    _HEALTH_DIR / "codex",
):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from hc_checker import ClaudeRunning  # noqa: E402
from hc_runner_factory import make_llm_runner  # noqa: E402
from mcp_config_builder import build_mcp_config  # noqa: E402

from harness.session_delegate_running import SessionDelegateRunning
from harness.step_run_outcome import StepRunOutcome

RunnerFactory = Callable[..., ClaudeRunning]
McpConfigBuilding = Callable[[Path], str]

_FLOW_TOOLS = "mcp__pipeline__flow_start,mcp__pipeline__flow_next,mcp__pipeline__flow_status"


class SessionDelegateRunner(SessionDelegateRunning):

    def __init__(
        self,
        plugin_root: Path,
        timeout: int,
        cwd_resolver: Callable[[], Path] = Path.cwd,
        runner_factory: RunnerFactory = make_llm_runner,
        mcp_config_builder: McpConfigBuilding = build_mcp_config,
    ) -> None:
        self._plugin_root = plugin_root
        self._timeout = timeout
        self._cwd_resolver = cwd_resolver
        self._runner_factory = runner_factory
        self._mcp_config_builder = mcp_config_builder

    def run(self, prompt: str) -> StepRunOutcome:
        runner = self._runner_factory(
            mcp_config=self._mcp_config_builder(self._plugin_root),
            allowed_tools=_FLOW_TOOLS,
            cwd=str(self._cwd_resolver()),
        )
        result = runner.run(prompt, self._timeout)
        if result is None:
            return StepRunOutcome(awaiting_input=False, rejection_reason="Delegated session produced no result")
        return StepRunOutcome(awaiting_input=False, outputs={})