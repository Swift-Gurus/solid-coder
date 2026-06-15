"""
solid-description: Verifies LocalLLMLogger's tool call logging, thinking recording, and error resilience.
solid-category: unit-test
"""

import json
import tempfile
import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

from hc_llama_runner import LocalLLMLogger, JsonlEntryWriter, MonotonicTimer  # noqa: E402

_SEARCH = "mcp__plugin_solid-coder_pipeline__search_codebase"


class TestLocalLLMLogger(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.logger = self._make_logger(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def _make_logger(self, tmp_dir: Path, session_id: str = "sess-abc") -> LocalLLMLogger:
        log_dir = tmp_dir / "llm-sessions" / session_id
        return LocalLLMLogger(log_dir=log_dir, file_path="/src/Foo.swift", model="Qwen3")

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
        self.logger.log_tool_call("call-123", _SEARCH, {"query": "UserRepo"})
        files = list(Path(self._tmp.name).rglob("call-123.jsonl"))
        self.assertEqual(len(files), 1)
        entries = self._read_jsonl(files[0])
        self.assertEqual(entries[0]["ev"], "call")
        self.assertEqual(entries[0]["name"], _SEARCH)

    def test_appends_result_to_call_file(self):
        self.logger.log_tool_call("call-123", _SEARCH, {"query": "Foo"})
        search_result = "tests/A.swift — Type A\ntests/B.swift — Type B\ntests/C.swift — Type C"
        self.logger.log_tool_result("call-123", _SEARCH, search_result)
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
        logger._writer = JsonlEntryWriter()
        logger._timer = MonotonicTimer()
        logger.log_start(100)
        logger.log_tool_call("x", _SEARCH, {})
        logger.log_tool_result("x", _SEARCH, "[]")
        logger.log_done(1, {}, [], thinking="some thinking")


if __name__ == "__main__":
    unittest.main()
