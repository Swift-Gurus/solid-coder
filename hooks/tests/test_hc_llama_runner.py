"""
solid-description: Unit tests for LlamaHttpClient, GatewayToolDispatcher, and LlamaServerRunner.
solid-category: unit-test
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

from hc_llama_runner import (
    GatewayToolDispatcher,
    LlamaHttpClient,
    LlamaServerRunner,
    LocalLLMLogger,
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
        file_searcher = MagicMock()
        file_searcher.grep_by_name.return_value = ""
        file_searcher.glob_by_name.return_value = ""
        return GatewayToolDispatcher(invoker=invoker, file_searcher=file_searcher), invoker, file_searcher

    def _extra_args(self, invoker) -> list:
        call = invoker.invoke.call_args
        return call[1].get("extra_args") or call[0][1]

    def test_search_codebase_invokes_correct_subcommand(self):
        d, invoker, _fs = self._make({"results": []})
        d.dispatch(_tc("mcp__pipeline__search_codebase", {"query": "UserRepository"}))
        self.assertEqual(invoker.invoke.call_args[0][0], "search_codebase")

    def test_search_codebase_passes_synonyms_not_query_flag(self):
        d, invoker, _fs = self._make({"results": []})
        d.dispatch(_tc("mcp__pipeline__search_codebase", {"query": "UserRepository"}))
        extra = self._extra_args(invoker)
        self.assertIn("--synonyms", extra)
        self.assertNotIn("--query", extra)
        self.assertIn("UserRepository", extra)

    def test_load_fix_invokes_correct_subcommand(self):
        d, invoker, _fs = self._make({"content": "fix"})
        d.dispatch(_tc("mcp__docs__load_fix_for_violation", {"metric_id": "OCP-1"}))
        self.assertEqual(invoker.invoke.call_args[0][0], "load_fix_for_violation")

    def test_load_fix_passes_metric_id_in_extra_args(self):
        d, invoker, _fs = self._make({"content": "fix"})
        d.dispatch(_tc("mcp__docs__load_fix_for_violation", {"metric_id": "OCP-1"}))
        self.assertIn("OCP-1", self._extra_args(invoker))

    def test_unknown_tool_returns_error_string(self):
        d, _, _fs = self._make()
        self.assertIn("unknown tool", d.dispatch(_tc("nonexistent", {})))

    def test_malformed_arguments_falls_back_to_empty_args(self):
        d, _, _fs = self._make(None)
        tc = {"id": "x", "function": {"name": "mcp__pipeline__search_codebase", "arguments": "not json"}}
        result = d.dispatch(tc)
        self.assertIsInstance(result, str)  # does not raise; falls back to empty query

    def test_arguments_as_dict_handled_gracefully(self):
        d, invoker, _fs = self._make({"results": []})
        tc = {"id": "x", "function": {"name": "mcp__pipeline__search_codebase", "arguments": {"query": "Foo"}}}
        d.dispatch(tc)
        self.assertIn("Foo", self._extra_args(invoker))

    def test_search_returns_json_string_of_result(self):
        d, _, _fs = self._make({"results": ["Foo.swift"]})
        self.assertIn("results", json.loads(d.dispatch(_tc("mcp__pipeline__search_codebase", {"query": "Foo"}))))

    def test_search_returns_empty_list_on_invoker_failure(self):
        d, _, _fs = self._make(None)
        self.assertEqual(d.dispatch(_tc("mcp__pipeline__search_codebase", {"query": "Foo"})), "[]")

    def test_load_fix_returns_content_string_not_json_encoded_dict(self):
        """LLM must receive plain content text with real newlines, not double-encoded JSON."""
        fix_content = "<fix>\nIntroduce a protocol.\n</fix>"
        d, invoker, _fs = self._make(
            {"principle": "OCP", "metric_id": "OCP-1", "content": fix_content}
        )
        result = d.dispatch(_tc("mcp__docs__load_fix_for_violation", {"metric_id": "OCP-1"}))
        # Result must be the raw string — real newlines, no \\n, no \" escapes
        self.assertEqual(result, fix_content)
        self.assertNotIn("\\n", result)
        self.assertNotIn('\\"', result)

    def test_load_fix_returns_empty_string_on_invoker_failure(self):
        d, _, _fs = self._make(None)
        self.assertEqual(d.dispatch(_tc("mcp__docs__load_fix_for_violation", {"metric_id": "OCP-1"})), "")

    def test_grep_codebase_delegates_to_file_searcher(self):
        d, _, fs = self._make()
        fs.grep_by_name.return_value = "/src/Foo.swift:1: class Foo"
        result = d.dispatch(_tc("mcp__pipeline__grep_codebase", {"name": "Foo"}))
        fs.grep_by_name.assert_called_once_with("Foo")
        self.assertEqual(result, "/src/Foo.swift:1: class Foo")

    def test_glob_codebase_delegates_to_file_searcher(self):
        d, _, fs = self._make()
        fs.glob_by_name.return_value = "/src/FooManager.swift"
        result = d.dispatch(_tc("mcp__pipeline__glob_codebase", {"pattern": "*Foo*"}))
        fs.glob_by_name.assert_called_once_with("*Foo*")
        self.assertEqual(result, "/src/FooManager.swift")


class TestLocalLLMLogger(unittest.TestCase):
    def _make_logger(self, tmp_dir: Path, session_id: str = "sess-abc") -> LocalLLMLogger:
        with patch("hc_llama_runner.Path.cwd", return_value=Path("/fake/myproject")):
            with patch.object(LocalLLMLogger, "ROOT", tmp_dir):
                return LocalLLMLogger(session_id=session_id, file_path="/src/Foo.swift", model="Qwen3")

    def _read_jsonl(self, path: Path) -> list:
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]

    def test_creates_exchange_file_on_log_start(self):
        with tempfile.TemporaryDirectory() as d:
            logger = self._make_logger(Path(d))
            logger.log_start(prompt_len=1000)
            files = list(Path(d).rglob("_exchange.jsonl"))
            self.assertEqual(len(files), 1)
            entries = self._read_jsonl(files[0])
            self.assertEqual(entries[0]["ev"], "start")
            self.assertEqual(entries[0]["file"], "Foo.swift")

    def test_creates_call_file_on_log_tool_call(self):
        with tempfile.TemporaryDirectory() as d:
            logger = self._make_logger(Path(d))
            logger.log_tool_call("call-123", "mcp__pipeline__search_codebase", {"query": "UserRepo"})
            files = list(Path(d).rglob("call-123.jsonl"))
            self.assertEqual(len(files), 1)
            entries = self._read_jsonl(files[0])
            self.assertEqual(entries[0]["ev"], "call")
            self.assertEqual(entries[0]["name"], "mcp__pipeline__search_codebase")

    def test_appends_result_to_call_file(self):
        with tempfile.TemporaryDirectory() as d:
            logger = self._make_logger(Path(d))
            logger.log_tool_call("call-123", "mcp__pipeline__search_codebase", {"query": "Foo"})
            logger.log_tool_result("call-123", "mcp__pipeline__search_codebase", json.dumps({"results": ["a", "b", "c"]}))
            entries = self._read_jsonl(list(Path(d).rglob("call-123.jsonl"))[0])
            self.assertEqual(len(entries), 2)
            self.assertEqual(entries[1]["ev"], "result")
            self.assertEqual(entries[1]["hits"], 3)

    def test_log_done_appends_to_exchange_file(self):
        with tempfile.TemporaryDirectory() as d:
            logger = self._make_logger(Path(d))
            logger.log_start(prompt_len=500)
            logger.log_done(rounds=1, usage={"prompt_tokens": 100, "completion_tokens": 20}, violations=[])
            entries = self._read_jsonl(list(Path(d).rglob("_exchange.jsonl"))[0])
            done = next(e for e in entries if e["ev"] == "done")
            self.assertEqual(done["result"], "clean")
            self.assertEqual(done["input_tokens"], 100)

    def test_log_done_marks_blocked_when_violations_present(self):
        with tempfile.TemporaryDirectory() as d:
            logger = self._make_logger(Path(d))
            logger.log_start(1)
            logger.log_done(1, {}, [{"principle": "SRP", "issue": "x", "fix": "y", "metric_id": "SRP-1"}])
            entries = self._read_jsonl(list(Path(d).rglob("_exchange.jsonl"))[0])
            done = next(e for e in entries if e["ev"] == "done")
            self.assertEqual(done["result"], "blocked")
            self.assertEqual(len(done["violations"]), 1)

    def test_session_dir_uses_session_id(self):
        with tempfile.TemporaryDirectory() as d:
            logger = self._make_logger(Path(d), session_id="my-session-xyz")
            logger.log_start(1)
            dirs = [p.name for p in Path(d).rglob("my-session-xyz") if p.is_dir()]
            self.assertIn("my-session-xyz", dirs)

    def test_never_raises_on_write_error(self):
        logger = LocalLLMLogger.__new__(LocalLLMLogger)
        logger._dir = Path("/nonexistent/path/that/does/not/exist")
        logger._file = "Foo.swift"
        logger._model = "Qwen3"
        logger._t0 = 0.0
        logger.log_start(100)
        logger.log_tool_call("x", "mcp__pipeline__search_codebase", {})
        logger.log_tool_result("x", "mcp__pipeline__search_codebase", "[]")
        logger.log_done(1, {}, [])


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
            _tool_call_response("mcp__pipeline__search_codebase", {"query": "Foo"}),
            _no_tool_response('{"violations": []}'),
        ])
        result = runner.run("prompt", 30)
        dispatcher.dispatch.assert_called_once()
        self.assertEqual(result, '{"violations": []}')

    def test_tool_result_appended_as_tool_message(self):
        runner, client, _ = self._make(
            [_tool_call_response("mcp__pipeline__search_codebase", {"query": "Foo"}),
             _no_tool_response("done")],
            dispatch_result='{"matches": ["Bar.swift"]}',
        )
        runner.run("prompt", 30)
        second_messages = client.chat.call_args_list[1][0][0]
        tool_msg = next(m for m in second_messages if m.get("role") == "tool")
        self.assertEqual(tool_msg["content"], '{"matches": ["Bar.swift"]}')

    def test_tool_call_id_threaded_into_tool_message(self):
        runner, client, _ = self._make([
            _tool_call_response("mcp__pipeline__search_codebase", {"query": "X"}, call_id="abc123"),
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
                _tc("mcp__pipeline__search_codebase", {"query": "A"}, call_id="a"),
                _tc("mcp__pipeline__search_codebase", {"query": "B"}, call_id="b"),
            ],
        }}]}
        runner, _, dispatcher = self._make([parallel, _no_tool_response("ok")])
        runner.run("prompt", 30)
        self.assertEqual(dispatcher.dispatch.call_count, 2)

    def test_returns_none_when_max_rounds_exceeded(self):
        runner, client, _ = self._make(
            [_tool_call_response("mcp__pipeline__search_codebase", {"query": "x"})] * 5,
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
