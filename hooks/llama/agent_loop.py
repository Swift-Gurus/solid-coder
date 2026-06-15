"""
solid-description: Executes an agentic conversation loop that processes messages and coordinates tool invocations until completion.
solid-category: service
solid-tags: [hook, llm]
"""

from typing import Optional, Protocol

from llama.http_client import LlamaHttpChatting
from llama.tool_dispatcher import TOOLS
from llama.tool_call_orchestrating import ToolCallOrchestrating
from llama.session_observer import LLMSessionObserving
from llama.builtin_range import RangeIterating, BuiltinRange
from llama.thinking_extractor import ThinkingExtracting, ThinkingExtractor


class AgentLoopExecuting(Protocol):
    def execute(
        self,
        messages: list,
        timeout: int,
        observer: Optional[LLMSessionObserving],
    ) -> tuple: ...


class AgentLoopExecutor:
    """Facade: drives the agent loop by coordinating LLM client, orchestrator, and thinker.

    All dependencies are protocol-typed — this class owns no domain logic of its own.
    Single responsibility: advance the loop one round at a time until the LLM stops
    requesting tool calls. Satisfies the SRP Facade exception.
    """

    def __init__(
        self,
        client: LlamaHttpChatting,
        orchestrator: ToolCallOrchestrating,
        thinker: ThinkingExtracting,
        max_rounds: int,
        range_iter: Optional[RangeIterating] = None,
    ) -> None:
        self._client = client
        self._orchestrator = orchestrator
        self._thinker = thinker
        self._max_rounds = max_rounds
        self._range: RangeIterating = range_iter or BuiltinRange()

    def execute(
        self,
        messages: list,
        timeout: int,
        observer: Optional[LLMSessionObserving],
    ) -> tuple:
        rounds = 0
        last_usage: dict = {}
        try:
            for _ in self._range.iterate(self._max_rounds):
                response = self._client.chat(messages, TOOLS, timeout)
                if response is None:
                    return None, {}, rounds, ""

                last_usage = response.get("usage", {})
                choice = response.get("choices", [{}])[0]
                message = choice.get("message", {})

                if choice.get("finish_reason") != "tool_calls":
                    thinking, content = self._thinker.extract(message)
                    return content, last_usage, rounds, thinking

                tool_calls = message.get("tool_calls") or []
                if not tool_calls:
                    return message.get("content", ""), last_usage, rounds, ""

                interim_thinking, _ = self._thinker.extract(message)
                if interim_thinking and observer:
                    observer.on_thinking(rounds + 1, interim_thinking)

                rounds += 1
                messages.append(message)
                self._orchestrator.orchestrate(tool_calls, messages, observer)
        except Exception:
            return None, {}, rounds, ""

        return None, last_usage, rounds, ""