"""
solid-description: Tests agent loop execution including tool dispatch, message threading, round limits, observer events, and thinking extraction.
solid-category: unit-test
"""

import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

from hc_llama_runner import LlamaServerRunner, AgentLoopExecutor  # noqa: E402
from llama.tool_call_orchestrator import ToolCallOrchestrator  # noqa: E402
from llama.tool_call_parser import ToolCallParser  # noqa: E402
from llama.thinking_extractor import ThinkingExtractor  # noqa: E402

_SEARCH = "mcp__plugin_solid-coder_pipeline__search_codebase"


def _tc(name: str, args: dict, call_id: str = "c1") -> dict:
    return {"id": call_id, "type": "function",
            "function": {"name": name, "arguments": json.dumps(args)}}


def _no_tool_response(content: str) -> dict:
    return {"choices": [{"finish_reason": "stop",
                         "message": {"role": "assistant", "content": content, "tool_calls": []}}]}


def _tool_call_response(name: str, args: dict, call_id: str = "call_1", content: str = "") -> dict:
    return {"choices": [{"finish_reason": "tool_calls", "message": {
        "role": "assistant", "content": content,
        "tool_calls": [_tc(name, args, call_id=call_id)],
    }}]}


class TestLlamaServerRunner(unittest.TestCase):
    def _make(self, responses: list, dispatch_result: str = "[]", max_rounds: int = 10):
        client = MagicMock()
        client.chat.side_effect = list(responses)
        dispatcher = MagicMock()
        dispatcher.dispatch.return_value = dispatch_result
        orchestrator = ToolCallOrchestrator(dispatcher=dispatcher, arg_parser=ToolCallParser())
        thinker = ThinkingExtractor()
        loop = AgentLoopExecutor(
            client=client, orchestrator=orchestrator, thinker=thinker, max_rounds=max_rounds
        )
        return LlamaServerRunner(loop=loop), client, dispatcher

    def test_returns_content_when_finish_is_stop(self):
        runner, _, _ = self._make([_no_tool_response("clean code")])
        self.assertEqual(runner.run("prompt", 30), "clean code")

    def test_dispatches_tool_call_and_returns_final_content(self):
        runner, _, dispatcher = self._make([
            _tool_call_response(_SEARCH, {"query": "Foo"}),
            _no_tool_response('{"violations": []}'),
        ])
        result = runner.run("prompt", 30)
        dispatcher.dispatch.assert_called_once()
        self.assertEqual(result, '{"violations": []}')

    def test_tool_result_appended_as_tool_message(self):
        runner, client, _ = self._make(
            [_tool_call_response(_SEARCH, {"query": "Foo"}),
             _no_tool_response("done")],
            dispatch_result='{"matches": ["Bar.swift"]}',
        )
        runner.run("prompt", 30)
        second_messages = client.chat.call_args_list[1][0][0]
        tool_msg = next(m for m in second_messages if m.get("role") == "tool")
        self.assertEqual(tool_msg["content"], '{"matches": ["Bar.swift"]}')

    def test_tool_call_id_threaded_into_tool_message(self):
        runner, client, _ = self._make([
            _tool_call_response(_SEARCH, {"query": "X"}, call_id="abc123"),
            _no_tool_response("done"),
        ])
        runner.run("prompt", 30)
        second_messages = client.chat.call_args_list[1][0][0]
        tool_msg = next(m for m in second_messages if m.get("role") == "tool")
        self.assertEqual(tool_msg["tool_call_id"], "abc123")

    def test_multiple_parallel_tool_calls_all_dispatched(self):
        parallel = {"choices": [{"finish_reason": "tool_calls", "message": {
            "role": "assistant", "content": "",
            "tool_calls": [
                _tc(_SEARCH, {"query": "A"}, call_id="a"),
                _tc(_SEARCH, {"query": "B"}, call_id="b"),
            ],
        }}]}
        runner, _, dispatcher = self._make([parallel, _no_tool_response("ok")])
        runner.run("prompt", 30)
        self.assertEqual(dispatcher.dispatch.call_count, 2)

    def test_returns_none_when_max_rounds_exceeded(self):
        runner, client, _ = self._make(
            [_tool_call_response(_SEARCH, {"query": "x"})] * 5,
            max_rounds=3,
        )
        self.assertIsNone(runner.run("prompt", 30))
        self.assertEqual(client.chat.call_count, 3)

    def test_returns_none_when_client_returns_none(self):
        runner, _, _ = self._make([None])
        self.assertIsNone(runner.run("prompt", 30))

    def test_returns_none_when_client_raises(self):
        client = MagicMock()
        client.chat.side_effect = RuntimeError("network error")
        orchestrator = ToolCallOrchestrator(dispatcher=MagicMock(), arg_parser=ToolCallParser())
        loop = AgentLoopExecutor(
            client=client, orchestrator=orchestrator, thinker=ThinkingExtractor(), max_rounds=3
        )
        runner = LlamaServerRunner(loop=loop)
        self.assertIsNone(runner.run("prompt", 30))

    def test_extracts_thinking_from_tool_call_round_and_notifies_observer(self):
        tool_round = _tool_call_response(
            _SEARCH, {"query": "Foo"}, content="<think>analyzing SRP cohesion</think>",
        )
        runner, _, _ = self._make([tool_round, _no_tool_response('{"violations": []}')])
        observer = MagicMock()
        runner._observer = observer
        runner.run("prompt", 30)
        observer.on_thinking.assert_called_once_with(1, "analyzing SRP cohesion")

    def test_no_observer_thinking_call_when_tool_round_has_no_think_block(self):
        tool_round = _tool_call_response(_SEARCH, {"query": "Foo"})
        runner, _, _ = self._make([tool_round, _no_tool_response('{"violations": []}')])
        observer = MagicMock()
        runner._observer = observer
        runner.run("prompt", 30)
        observer.on_thinking.assert_not_called()

    def test_thinking_round_number_increments_across_rounds(self):
        tool_round1 = _tool_call_response(
            _SEARCH, {"query": "A"}, content="<think>round 1 thought</think>",
        )
        tool_round2 = _tool_call_response(
            _SEARCH, {"query": "B"}, content="<think>round 2 thought</think>",
        )
        runner, _, _ = self._make([tool_round1, tool_round2, _no_tool_response("done")])
        observer = MagicMock()
        runner._observer = observer
        runner.run("prompt", 30)
        calls = observer.on_thinking.call_args_list
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0], unittest.mock.call(1, "round 1 thought"))
        self.assertEqual(calls[1], unittest.mock.call(2, "round 2 thought"))

    def test_strips_think_block_from_returned_content(self):
        raw = "<think>reasoning</think>\n\n{\"violations\": []}"
        runner, _, _ = self._make([_no_tool_response(raw)])
        result = runner.run("prompt", 30)
        self.assertEqual(result, '{"violations": []}')
        self.assertNotIn("<think>", result)

    def test_passes_thinking_to_observer_on_done(self):
        raw = "<think>deep analysis</think>\n\n{\"violations\": []}"
        runner, _, _ = self._make([_no_tool_response(raw)])
        observer = MagicMock()
        runner._observer = observer
        runner.run("prompt", 30)
        call_kwargs = observer.on_done.call_args
        thinking_arg = call_kwargs[1].get("thinking") or (call_kwargs[0][3] if len(call_kwargs[0]) > 3 else "")
        self.assertEqual(thinking_arg, "deep analysis")

    def test_observer_on_done_called_with_empty_thinking_when_no_think_block(self):
        runner, _, _ = self._make([_no_tool_response('{"violations": []}')])
        observer = MagicMock()
        runner._observer = observer
        runner.run("prompt", 30)
        call_kwargs = observer.on_done.call_args
        thinking_arg = call_kwargs[1].get("thinking", None)
        self.assertEqual(thinking_arg, "")


if __name__ == "__main__":
    unittest.main()
