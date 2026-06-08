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
    AgentLoopExecutor,
    FileSearcher,
    GatewayToolDispatcher,
    LlamaHttpClient,
    LlamaServerRunner,
    LocalLLMLogger,
    TOOLS,
    _extract_thinking_and_content,
    _strip_thinking,
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


def _tool_call_response(name: str, args: dict, call_id: str = "call_1", content: str = "") -> dict:
    return {"choices": [{"finish_reason": "tool_calls", "message": {
        "role": "assistant", "content": content,
        "tool_calls": [_tc(name, args, call_id=call_id)],
    }}]}


class TestExtractThinkingAndContent(unittest.TestCase):
    def test_returns_reasoning_content_field_when_present(self):
        msg = {"reasoning_content": "model reasoning here", "content": "final answer"}
        thinking, content = _extract_thinking_and_content(msg)
        self.assertEqual(thinking, "model reasoning here")
        self.assertEqual(content, "final answer")

    def test_falls_back_to_think_tag_stripping_when_no_reasoning_content(self):
        msg = {"content": "<think>inline reasoning</think>\nfinal answer"}
        thinking, content = _extract_thinking_and_content(msg)
        self.assertEqual(thinking, "inline reasoning")
        self.assertEqual(content, "final answer")

    def test_prefers_reasoning_content_over_think_tags(self):
        msg = {"reasoning_content": "from field", "content": "<think>from tag</think>answer"}
        thinking, _ = _extract_thinking_and_content(msg)
        self.assertEqual(thinking, "from field")

    def test_returns_empty_thinking_when_neither_source_present(self):
        msg = {"content": "plain answer"}
        thinking, content = _extract_thinking_and_content(msg)
        self.assertEqual(thinking, "")
        self.assertEqual(content, "plain answer")

    def test_handles_empty_message(self):
        thinking, content = _extract_thinking_and_content({})
        self.assertEqual(thinking, "")
        self.assertEqual(content, "")

    def test_strips_whitespace_from_reasoning_content(self):
        msg = {"reasoning_content": "  padded reasoning  ", "content": "answer"}
        thinking, _ = _extract_thinking_and_content(msg)
        self.assertEqual(thinking, "padded reasoning")


class TestStripThinking(unittest.TestCase):
    def test_returns_empty_thinking_and_content_unchanged_when_no_think_block(self):
        thinking, response = _strip_thinking('{"violations": []}')
        self.assertEqual(thinking, "")
        self.assertEqual(response, '{"violations": []}')

    def test_strips_think_block_and_returns_both_parts(self):
        raw = "<think>reasoning here</think>\n\n{\"violations\": []}"
        thinking, response = _strip_thinking(raw)
        self.assertEqual(thinking, "reasoning here")
        self.assertEqual(response, '{"violations": []}')

    def test_trims_whitespace_from_thinking_and_response(self):
        raw = "<think>  reasoning  </think>   {\"violations\": []}"
        thinking, response = _strip_thinking(raw)
        self.assertEqual(thinking, "reasoning")
        self.assertEqual(response, '{"violations": []}')

    def test_multiline_thinking_block(self):
        raw = "<think>\nStep 1: check SRP\nStep 2: check OCP\n</think>\n\n{\"violations\": []}"
        thinking, response = _strip_thinking(raw)
        self.assertIn("Step 1", thinking)
        self.assertIn("Step 2", thinking)
        self.assertEqual(response, '{"violations": []}')

    def test_empty_think_block_returns_empty_thinking(self):
        raw = "<think>\n\n</think>\n\n{\"violations\": []}"
        thinking, response = _strip_thinking(raw)
        self.assertEqual(thinking, "")
        self.assertEqual(response, '{"violations": []}')

    def test_empty_string_returns_empty_pair(self):
        thinking, response = _strip_thinking("")
        self.assertEqual(thinking, "")
        self.assertEqual(response, "")

    def test_content_without_json_returned_intact(self):
        thinking, response = _strip_thinking("plain text response")
        self.assertEqual(thinking, "")
        self.assertEqual(response, "plain text response")


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
        file_searcher.search_codebase.return_value = ""
        file_searcher.read_file.return_value = ""
        return GatewayToolDispatcher(invoker=invoker, file_searcher=file_searcher), invoker, file_searcher

    def _extra_args(self, invoker) -> list:
        call = invoker.invoke.call_args
        return call[1].get("extra_args") or call[0][1]

    def test_search_codebase_delegates_to_file_searcher(self):
        d, _, fs = self._make()
        fs.search_codebase.return_value = "tests/Foo.swift — Foo service"
        result = d.dispatch(_tc("mcp__pipeline__search_codebase", {"query": "Foo service repository"}))
        fs.search_codebase.assert_called_once_with("Foo service repository")
        self.assertEqual(result, "tests/Foo.swift — Foo service")

    def test_read_file_delegates_to_file_searcher(self):
        d, _, fs = self._make()
        fs.read_file.return_value = "class Foo {}"
        result = d.dispatch(_tc("mcp__pipeline__read_file", {"file_path": "/src/Foo.swift"}))
        fs.read_file.assert_called_once_with("/src/Foo.swift")
        self.assertEqual(result, "class Foo {}")

    def test_read_file_does_not_use_invoker(self):
        d, invoker, _ = self._make()
        d.dispatch(_tc("mcp__pipeline__read_file", {"file_path": "/src/Foo.swift"}))
        invoker.invoke.assert_not_called()

    def test_search_codebase_does_not_use_invoker(self):
        d, invoker, _ = self._make()
        d.dispatch(_tc("mcp__pipeline__search_codebase", {"query": "Foo"}))
        invoker.invoke.assert_not_called()

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
        d, _, fs = self._make()
        fs.search_codebase.return_value = ""
        tc = {"id": "x", "function": {"name": "mcp__pipeline__search_codebase", "arguments": {"query": "Foo"}}}
        d.dispatch(tc)
        fs.search_codebase.assert_called_once_with("Foo")

    def test_search_returns_file_searcher_result_directly(self):
        d, _, fs = self._make()
        fs.search_codebase.return_value = "tests/Foo.swift — Foo type"
        result = d.dispatch(_tc("mcp__pipeline__search_codebase", {"query": "Foo"}))
        self.assertEqual(result, "tests/Foo.swift — Foo type")

    def test_search_returns_empty_string_when_file_searcher_returns_empty(self):
        d, _, fs = self._make()
        fs.search_codebase.return_value = ""
        self.assertEqual(d.dispatch(_tc("mcp__pipeline__search_codebase", {"query": "Foo"})), "")

    def test_load_fix_returns_content_string_not_json_encoded_dict(self):
        """Invoker extracts content key; LLM receives plain text with real newlines."""
        fix_content = "<fix>\nIntroduce a protocol.\n</fix>"
        d, _, _fs = self._make(fix_content)
        result = d.dispatch(_tc("mcp__docs__load_fix_for_violation", {"metric_id": "OCP-1"}))
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


class TestFileSearcher(unittest.TestCase):
    def test_search_codebase_delegates_to_injected_search_fn(self):
        search_fn = MagicMock(return_value="tests/Foo.swift — Foo service")
        fs = FileSearcher(search_fn=search_fn)
        result = fs.search_codebase("Foo service repository")
        search_fn.assert_called_once_with("Foo service repository")
        self.assertEqual(result, "tests/Foo.swift — Foo service")

    def test_search_codebase_returns_empty_string_when_search_fn_returns_empty(self):
        fs = FileSearcher(search_fn=lambda q: "")
        self.assertEqual(fs.search_codebase("anything"), "")

    def test_read_file_delegates_to_injected_read_fn(self):
        read_fn = MagicMock(return_value="class Foo {}")
        fs = FileSearcher(read_fn=read_fn)
        result = fs.read_file("/src/Foo.swift")
        read_fn.assert_called_once_with("/src/Foo.swift")
        self.assertEqual(result, "class Foo {}")

    def test_read_file_returns_error_string_on_os_error(self):
        fs = FileSearcher(read_fn=lambda p: f"error: [Errno 2] No such file: '{p}'")
        result = fs.read_file("/nonexistent/Foo.swift")
        self.assertIn("error", result)


class TestLocalLLMLogger(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.logger = self._make_logger(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def _make_logger(self, tmp_dir: Path, session_id: str = "sess-abc") -> LocalLLMLogger:
        with patch("hc_llama_runner.solid_coder_project_dir", return_value=tmp_dir):
            return LocalLLMLogger(session_id=session_id, file_path="/src/Foo.swift", model="Qwen3")

    def _read_jsonl(self, path: Path) -> list:
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]

    def _get_done_entry(self, d: Path) -> dict:
        entries = self._read_jsonl(list(d.rglob("_exchange.jsonl"))[0])
        return next(e for e in entries if e["ev"] == "done")

    def test_creates_exchange_file_on_log_start(self):
        self.logger.log_start(prompt_len=1000)
        files = list(Path(self._tmp.name).rglob("_exchange.jsonl"))
        self.assertEqual(len(files), 1)
        entries = self._read_jsonl(files[0])
        self.assertEqual(entries[0]["ev"], "start")
        self.assertEqual(entries[0]["file"], "Foo.swift")

    def test_creates_call_file_on_log_tool_call(self):
        self.logger.log_tool_call("call-123", "mcp__pipeline__search_codebase", {"query": "UserRepo"})
        files = list(Path(self._tmp.name).rglob("call-123.jsonl"))
        self.assertEqual(len(files), 1)
        entries = self._read_jsonl(files[0])
        self.assertEqual(entries[0]["ev"], "call")
        self.assertEqual(entries[0]["name"], "mcp__pipeline__search_codebase")

    def test_appends_result_to_call_file(self):
        self.logger.log_tool_call("call-123", "mcp__pipeline__search_codebase", {"query": "Foo"})
        search_result = "tests/A.swift — Type A\ntests/B.swift — Type B\ntests/C.swift — Type C"
        self.logger.log_tool_result("call-123", "mcp__pipeline__search_codebase", search_result)
        entries = self._read_jsonl(list(Path(self._tmp.name).rglob("call-123.jsonl"))[0])
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[1]["ev"], "result")
        self.assertEqual(entries[1]["hits"], 3)

    def test_log_done_appends_to_exchange_file(self):
        self.logger.log_start(prompt_len=500)
        self.logger.log_done(rounds=1, usage={"prompt_tokens": 100, "completion_tokens": 20}, violations=[])
        done = self._get_done_entry(Path(self._tmp.name))
        self.assertEqual(done["result"], "clean")
        self.assertEqual(done["input_tokens"], 100)

    def test_log_done_marks_blocked_when_violations_present(self):
        self.logger.log_start(1)
        self.logger.log_done(1, {}, [{"principle": "SRP", "issue": "x", "fix": "y", "metric_id": "SRP-1"}])
        done = self._get_done_entry(Path(self._tmp.name))
        self.assertEqual(done["result"], "blocked")
        self.assertEqual(len(done["violations"]), 1)

    def test_session_dir_uses_session_id(self):
        logger = self._make_logger(Path(self._tmp.name), session_id="my-session-xyz")
        logger.log_start(1)
        dirs = [p.name for p in Path(self._tmp.name).rglob("my-session-xyz") if p.is_dir()]
        self.assertIn("my-session-xyz", dirs)

    def test_log_thinking_writes_round_and_content_to_thinking_jsonl(self):
        self.logger.log_thinking(round=1, content="step 1: check SRP cohesion groups")
        files = list(Path(self._tmp.name).rglob("_thinking.jsonl"))
        self.assertEqual(len(files), 1)
        entries = self._read_jsonl(files[0])
        self.assertEqual(entries[0]["ev"], "thinking")
        self.assertEqual(entries[0]["round"], 1)
        self.assertEqual(entries[0]["content"], "step 1: check SRP cohesion groups")

    def test_log_thinking_appends_multiple_rounds(self):
        self.logger.log_thinking(1, "round 1 reasoning")
        self.logger.log_thinking(2, "round 2 reasoning")
        entries = self._read_jsonl(list(Path(self._tmp.name).rglob("_thinking.jsonl"))[0])
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["round"], 1)
        self.assertEqual(entries[1]["round"], 2)

    def test_log_done_writes_thinking_len_when_thinking_present(self):
        self.logger.log_start(1)
        self.logger.log_done(1, {}, [], thinking="model reasoned about SRP")
        done = self._get_done_entry(Path(self._tmp.name))
        self.assertIn("thinking_len", done)
        self.assertEqual(done["thinking_len"], len("model reasoned about SRP"))

    def test_log_done_writes_thinking_to_separate_jsonl_file(self):
        self.logger.log_start(1)
        self.logger.log_done(1, {}, [], thinking="check OCP: sealed point found")
        thinking_files = list(Path(self._tmp.name).rglob("_thinking.jsonl"))
        self.assertEqual(len(thinking_files), 1)
        entries = self._read_jsonl(thinking_files[0])
        self.assertEqual(entries[0]["ev"], "thinking")
        self.assertEqual(entries[0]["content"], "check OCP: sealed point found")

    def test_log_done_omits_thinking_len_when_thinking_empty(self):
        self.logger.log_start(1)
        self.logger.log_done(1, {}, [])
        done = self._get_done_entry(Path(self._tmp.name))
        self.assertNotIn("thinking_len", done)
        self.assertFalse(list(Path(self._tmp.name).rglob("_thinking.jsonl")))

    def test_never_raises_on_write_error(self):
        logger = LocalLLMLogger.__new__(LocalLLMLogger)
        logger._dir = Path("/nonexistent/path/that/does/not/exist")
        logger._file = "Foo.swift"
        logger._model = "Qwen3"
        logger._t0 = 0.0
        logger.log_start(100)
        logger.log_tool_call("x", "mcp__pipeline__search_codebase", {})
        logger.log_tool_result("x", "mcp__pipeline__search_codebase", "[]")
        logger.log_done(1, {}, [], thinking="some thinking")


class TestLlamaServerRunner(unittest.TestCase):
    def _make(self, responses: list, dispatch_result: str = "[]", max_rounds: int = 10):
        client = MagicMock()
        client.chat.side_effect = list(responses)
        dispatcher = MagicMock()
        dispatcher.dispatch.return_value = dispatch_result
        loop = AgentLoopExecutor(client=client, dispatcher=dispatcher, max_rounds=max_rounds)
        return LlamaServerRunner(loop=loop), client, dispatcher

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
        loop = AgentLoopExecutor(client=client, dispatcher=MagicMock())
        runner = LlamaServerRunner(loop=loop)
        self.assertIsNone(runner.run("prompt", 30))

    def test_extracts_thinking_from_tool_call_round_and_notifies_observer(self):
        tool_round = _tool_call_response(
            "mcp__pipeline__search_codebase", {"query": "Foo"},
            content="<think>analyzing SRP cohesion</think>",
        )
        runner, _, _ = self._make([tool_round, _no_tool_response('{"violations": []}')])
        observer = MagicMock()
        runner._observer = observer
        runner.run("prompt", 30)
        observer.on_thinking.assert_called_once_with(1, "analyzing SRP cohesion")

    def test_no_observer_thinking_call_when_tool_round_has_no_think_block(self):
        tool_round = _tool_call_response("mcp__pipeline__search_codebase", {"query": "Foo"})
        runner, _, _ = self._make([tool_round, _no_tool_response('{"violations": []}')])
        observer = MagicMock()
        runner._observer = observer
        runner.run("prompt", 30)
        observer.on_thinking.assert_not_called()

    def test_thinking_round_number_increments_across_rounds(self):
        tool_round1 = _tool_call_response(
            "mcp__pipeline__search_codebase", {"query": "A"},
            content="<think>round 1 thought</think>",
        )
        tool_round2 = _tool_call_response(
            "mcp__pipeline__search_codebase", {"query": "B"},
            content="<think>round 2 thought</think>",
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
