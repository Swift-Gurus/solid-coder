"""
solid-description: Adapts a Claude callable to the ClaudeRunning protocol with MCP config and tool list.
solid-category: service
solid-tags: [hook, llm]
"""

import sys
from pathlib import Path
_MCP_DIR = Path(__file__).resolve().parents[2]
_MODULE_DIR = Path(__file__).resolve().parent
for _d in (_MCP_DIR, _MODULE_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from typing import Callable, Optional, Protocol

from hook_callable import CallableAdapting

ClaudeCallable = Callable[..., Optional[str]]


class ClaudeRunning(Protocol):
    def run(self, prompt: str, timeout: int) -> Optional[str]: ...


class ClaudeRunner(CallableAdapting):
    """Adapts a ClaudeCallable to the ClaudeRunning protocol, owning MCP config and tool list."""

    def __init__(
        self,
        mcp_config: str,
        allowed_tools: str,
        fn: ClaudeCallable,
        model: str = "",
    ) -> None:
        super().__init__(fn)
        self._mcp_config = mcp_config
        self._allowed_tools = allowed_tools
        self._model = model

    def run(self, prompt: str, timeout: int) -> Optional[str]:
        return self._strict_call(
            prompt,
            mcp_config=self._mcp_config,
            allowed_tools=self._allowed_tools,
            model=self._model,
            timeout=timeout,
        )
