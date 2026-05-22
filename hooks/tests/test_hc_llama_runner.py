"""
solid-description: Unit tests for LlamaHttpClient, GatewayToolDispatcher, and LlamaServerRunner.
solid-category: unit-test
"""

import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

from hc_llama_runner import (
    GatewayToolDispatcher,
    LlamaHttpClient,
    LlamaServerRunner,
    TOOLS,
)


def _urlopen_mock(body: dict):
    cm = MagicMock()
    cm.__enter__.return_value.read.return_value = json.dumps(body).encode()
    return cm


def _tc(name: str, args: dict, call_id: str = "c1") -> dict:
    return {"id": call_id, "type": "function",
            "function": {"name": name, "arguments": json.dumps(args)}}


def _no_tool_response(content: str) -> dict:
    return {"choices": [{"finish_reason": "stop",
                         "message": {"role": "assistant", "content": content, "tool_calls": []}}]}


def _tool_call_response(name: str, args: dict, call_id: str = "call_1") -> dict:
    return {"choices": [{"finish_reason": "tool_calls", "message": {
        "role": "assistant", "content": "",
        "tool_calls": [_tc(name, args, call_id=call_id)],
    }}]}


class TestLlamaHttpClient(unittest.TestCase):
    def setUp(self):
        self.client = LlamaHttpClient(host="http://localhost:8080", model="local")

    def test_returns_parsed_response_on_success(self):
        body = _no_tool_response("ok")
        with patch("urllib.request.urlopen", return_value=_urlopen_mock(body)):
            result = self.client.chat([{"role": "user", "content": "hi"}], TOOLS, 30)
        self.assertEqual(result, body)

    def test_returns_none_on_connection_error(self):
        with patch("urllib.request.urlopen", side_effect=OSError("refused")):
            self.assertIsNone(self.client.chat([], TOOLS, 30))

    def test_returns_none_on_json_decode_error(self):
        cm = MagicMock()
        cm.__enter__.return_value.read.return_value = b"not json"
        with patch("urllib.request.urlopen", return_value=cm):
            self.assertIsNone(self.client.chat([], TOOLS, 30))

    def test_posts_to_v1_chat_completions(self):
        captured = []
        def fake_open(req, timeout=None):
            captured.append(req.full_url)
            return _urlopen_mock(_no_tool_response("x"))
        with patch("urllib.request.urlopen", side_effect=fake_open):
            self.client.chat([], TOOLS, 30)
        self.assertIn("/v1/chat/completions", captured[0])

    def test_includes_tools_in_request_body(self):
        captured = []
        def fake_open(req, timeout=None):
            captured.append(json.loads(req.data))
            return _urlopen_mock(_no_tool_response("x"))
        with patch("urllib.request.urlopen", side_effect=fake_open):
            self.client.chat([], TOOLS, 30)
        self.assertEqual(len(captured[0]["tools"]), len(TOOLS))


class TestGatewayToolDispatcher(unittest.TestCase):
    def _make(self, return_value=None):
        invoker = MagicMock()
        invoker.invoke.return_value = return_value
        return GatewayToolDispatcher(invoker=invoker), invoker

    def _extra_args(self, invoker) -> list:
        call = invoker.invoke.call_args
        return call[1].get("extra_args") or call[0][1]

    def test_search_codebase_invokes_correct_subcommand(self):
        d, invoker = self._make({"results": []})
        d.dispatch(_tc("search_codebase", {"query": "UserRepository"}))
        self.assertEqual(invoker.invoke.call_args[0][0], "search_codebase")

    def test_search_codebase_passes_query_in_extra_args(self):
        d, invoker = self._make({"results": []})
        d.dispatch(_tc("search_codebase", {"query": "UserRepository"}))
        self.assertIn("UserRepository", self._extra_args(invoker))

    def test_load_fix_invokes_correct_subcommand(self):
        d, invoker = self._make({"content": "fix"})
        d.dispatch(_tc("load_fix_for_violation", {"metric_id": "OCP-1"}))
        self.assertEqual(invoker.invoke.call_args[0][0], "load_fix_for_violation")

    def test_load_fix_passes_metric_id_in_extra_args(self):
        d, invoker = self._make({"content": "fix"})
        d.dispatch(_tc("load_fix_for_violation", {"metric_id": "OCP-1"}))
        self.assertIn("OCP-1", self._extra_args(invoker))

    def test_unknown_tool_returns_error_string(self):
        d, _ = self._make()
        self.assertIn("unknown tool", d.dispatch(_tc("nonexistent", {})))

    def test_malformed_arguments_returns_error_string(self):
        d, _ = self._make()
        tc = {"id": "x", "function": {"name": "search_codebase", "arguments": "not json"}}
        self.assertIn("error", d.dispatch(tc))

    def test_arguments_as_dict_handled_gracefully(self):
        d, invoker = self._make({"results": []})
        tc = {"id": "x", "function": {"name": "search_codebase", "arguments": {"query": "Foo"}}}
        d.dispatch(tc)
        self.assertIn("Foo", self._extra_args(invoker))

    def test_search_returns_json_string_of_result(self):
        d, _ = self._make({"results": ["Foo.swift"]})
        self.assertIn("results", json.loads(d.dispatch(_tc("search_codebase", {"query": "Foo"}))))

    def test_search_returns_empty_list_on_invoker_failure(self):
        d, _ = self._make(None)
        self.assertEqual(d.dispatch(_tc("search_codebase", {"query": "Foo"})), "[]")


class TestLlamaServerRunner(unittest.TestCase):
    def _make(self, responses: list, dispatch_result: str = "[]", max_rounds: int = 10):
        client = MagicMock()
        client.chat.side_effect = list(responses)
        dispatcher = MagicMock()
        dispatcher.dispatch.return_value = dispatch_result
        return LlamaServerRunner(client=client, dispatcher=dispatcher, max_rounds=max_rounds), client, dispatcher

    def test_returns_content_when_finish_is_stop(self):
        runner, _, _ = self._make([_no_tool_response("clean code")])
        self.assertEqual(runner.run("prompt", 30), "clean code")

    def test_dispatches_tool_call_and_returns_final_content(self):
        runner, _, dispatcher = self._make([
            _tool_call_response("search_codebase", {"query": "Foo"}),
            _no_tool_response('{"violations": []}'),
        ])
        result = runner.run("prompt", 30)
        dispatcher.dispatch.assert_called_once()
        self.assertEqual(result, '{"violations": []}')

    def test_tool_result_appended_as_tool_message(self):
        runner, client, _ = self._make(
            [_tool_call_response("search_codebase", {"query": "Foo"}),
             _no_tool_response("done")],
            dispatch_result='{"matches": ["Bar.swift"]}',
        )
        runner.run("prompt", 30)
        second_messages = client.chat.call_args_list[1][0][0]
        tool_msg = next(m for m in second_messages if m.get("role") == "tool")
        self.assertEqual(tool_msg["content"], '{"matches": ["Bar.swift"]}')

    def test_tool_call_id_threaded_into_tool_message(self):
        runner, client, _ = self._make([
            _tool_call_response("search_codebase", {"query": "X"}, call_id="abc123"),
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
                _tc("search_codebase", {"query": "A"}, call_id="a"),
                _tc("search_codebase", {"query": "B"}, call_id="b"),
            ],
        }}]}
        runner, _, dispatcher = self._make([parallel, _no_tool_response("ok")])
        runner.run("prompt", 30)
        self.assertEqual(dispatcher.dispatch.call_count, 2)

    def test_returns_none_when_max_rounds_exceeded(self):
        runner, client, _ = self._make(
            [_tool_call_response("search_codebase", {"query": "x"})] * 5,
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
        runner = LlamaServerRunner(client=client, dispatcher=MagicMock())
        self.assertIsNone(runner.run("prompt", 30))


if __name__ == "__main__":
    unittest.main()
