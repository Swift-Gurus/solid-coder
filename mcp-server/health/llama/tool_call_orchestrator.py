"""
solid-description: Executes tool calls and integrates their results into the conversation.
solid-category: service
solid-tags: [hook, llm]
"""

from typing import Optional

from llama.tool_dispatcher import ToolDispatching
from llama.tool_call_parser import ToolCallArgsParsing
from llama.session_observer import LLMSessionObserving


class ToolCallOrchestrator:
    """Processes one round of tool calls: dispatch → observe → append results."""

    def __init__(
        self,
        dispatcher: ToolDispatching,
        arg_parser: ToolCallArgsParsing,
    ) -> None:
        self._dispatcher = dispatcher
        self._arg_parser = arg_parser

    def orchestrate(
        self,
        tool_calls: list,
        messages: list,
        observer: Optional[LLMSessionObserving],
    ) -> None:
        for tc in tool_calls:
            call_id = tc.get("id", "unknown")
            tc_args = self._arg_parser.parse(tc)
            tc_name = tc.get("function", {}).get("name", "")
            if observer:
                observer.on_tool_call(call_id, tc_name, tc_args)
            result_str = self._dispatcher.dispatch(tc)
            if observer:
                observer.on_tool_result(call_id, tc_name, result_str)
            messages.append({
                "role": "tool",
                "tool_call_id": call_id,
                "content": result_str,
            })