"""
solid-description: Observes and logs LLM session lifecycle events.
solid-category: service
solid-tags: [hook, llm]
"""

from typing import Protocol


class LocalLLMLogging(Protocol):
    def log_start(self, prompt_len: int) -> None: ...
    def log_tool_call(self, call_id: str, name: str, args: dict) -> None: ...
    def log_tool_result(self, call_id: str, name: str, result_str: str) -> None: ...
    def log_thinking(self, round: int, content: str) -> None: ...
    def log_done(self, rounds: int, usage: dict, violations: list, thinking: str = "") -> None: ...


class LLMSessionObserving(Protocol):
    def on_start(self, prompt_len: int) -> None: ...
    def on_tool_call(self, call_id: str, name: str, args: dict) -> None: ...
    def on_tool_result(self, call_id: str, name: str, result: str) -> None: ...
    def on_thinking(self, round: int, content: str) -> None: ...
    def on_done(self, rounds: int, usage: dict, violations: list, thinking: str = "") -> None: ...


class LLMSessionObserver:
    """Delegates all session events to LocalLLMLogger. Single cohesion group: logging only."""

    def __init__(self, logger: LocalLLMLogging) -> None:
        self._logger = logger

    def on_start(self, prompt_len: int) -> None:
        self._logger.log_start(prompt_len)

    def on_tool_call(self, call_id: str, name: str, args: dict) -> None:
        self._logger.log_tool_call(call_id, name, args)

    def on_tool_result(self, call_id: str, name: str, result: str) -> None:
        self._logger.log_tool_result(call_id, name, result)

    def on_thinking(self, round: int, content: str) -> None:
        self._logger.log_thinking(round, content)

    def on_done(self, rounds: int, usage: dict, violations: list, thinking: str = "") -> None:
        self._logger.log_done(rounds, usage, violations, thinking=thinking)
