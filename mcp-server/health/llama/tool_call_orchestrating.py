"""
solid-description: Protocol for orchestrating tool calls with optional session observation.
solid-category: utility
solid-tags: [hook, llm]
"""

from typing import Optional, Protocol

from llama.session_observer import LLMSessionObserving


class ToolCallOrchestrating(Protocol):
    def orchestrate(
        self,
        tool_calls: list,
        messages: list,
        observer: Optional[LLMSessionObserving],
    ) -> None: ...
