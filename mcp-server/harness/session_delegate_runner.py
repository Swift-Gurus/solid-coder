from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

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

from harness.json_loading import JsonLoading
from harness.session_delegate_running import SessionDelegateRunning
from harness.step_run_outcome import StepRunOutcome
from hc_checker import ClaudeRunning
from hc_runner_factory import make_llm_runner

RunnerFactory = Callable[..., ClaudeRunning]
_FLOW_TOOLS = (
    "mcp__solid-coder-flow-engine__flow_start,mcp__solid-coder-flow-engine__flow_next"
)


"""
solid-name: SessionDelegateRunner
solid-category: service
solid-spec: [SPEC-027, SPEC-037]
solid-description: Executes a prompt in a configured session and parses its declared output object.
"""


class SessionDelegateRunner(SessionDelegateRunning):
    def __init__(
        self,
        mcp_config: str,
        timeout: int,
        output_loader: JsonLoading,
        cwd_resolver: Callable[[], Path] = Path.cwd,
        runner_factory: RunnerFactory = make_llm_runner,
    ) -> None:
        self._mcp_config = mcp_config
        self._timeout = timeout
        self._output_loader = output_loader
        self._cwd_resolver = cwd_resolver
        self._runner_factory = runner_factory

    def run(self, prompt: str) -> StepRunOutcome:
        runner = self._runner_factory(
            mcp_config=self._mcp_config,
            allowed_tools=_FLOW_TOOLS,
            cwd=str(self._cwd_resolver()),
        )
        result = runner.run(prompt, self._timeout)
        if result is None:
            return StepRunOutcome(
                awaiting_input=False,
                rejection_reason="Delegated session produced no result",
            )
        try:
            outputs = self._output_loader.safe_load(result)
        except (TypeError, ValueError):
            outputs = None
        if not isinstance(outputs, dict):
            return StepRunOutcome(
                awaiting_input=False,
                rejection_reason="Delegated session must return one JSON object",
            )
        return StepRunOutcome(awaiting_input=False, outputs=outputs)
