"""Tests for PermissionPayloadBuilder and SlackPermissionNotifier."""

import sys
import unittest
from pathlib import Path

HOOKS_DIR = str(Path(__file__).resolve().parents[1])
if HOOKS_DIR not in sys.path:
    sys.path.insert(0, HOOKS_DIR)

from slack_notify import (
    EnvConfigReader,
    PermissionPayloadBuilder,
    SlackPermissionNotifier,
    WebhookDispatcher,
    _summarise_tool_input,
)


class FakeEnv:
    def __init__(self, values): self._v = values
    def get(self, k, d=""): return self._v.get(k, d)


class RecordingHttpSender:
    def __init__(self): self.calls = []
    def send(self, url, data, headers, timeout): self.calls.append((url, data))
    def return_bytes(self): return b""


class TestSummariseToolInput(unittest.TestCase):
    def test_write_returns_file_path(self):
        self.assertEqual(_summarise_tool_input("Write", {"file_path": "/a/b.swift"}), "/a/b.swift")

    def test_bash_returns_command(self):
        self.assertEqual(_summarise_tool_input("Bash", {"command": "git push"}), "git push")

    def test_bash_truncates_at_120(self):
        long = "x" * 150
        result = _summarise_tool_input("Bash", {"command": long})
        self.assertEqual(len(result), 121)
        self.assertTrue(result.endswith("…"))

    def test_webfetch_returns_url(self):
        self.assertEqual(_summarise_tool_input("WebFetch", {"url": "https://x.com"}), "https://x.com")

    def test_unknown_tool_returns_first_string_value(self):
        self.assertEqual(_summarise_tool_input("Custom", {"foo": "bar"}), "bar")

    def test_empty_input_returns_empty(self):
        self.assertEqual(_summarise_tool_input("Read", {}), "")


class TestPermissionPayloadBuilder(unittest.TestCase):
    def _build(self, tool_name, tool_input=None, cwd="/p/proj"):
        return PermissionPayloadBuilder(
            {"tool_name": tool_name, "tool_input": tool_input or {}, "cwd": cwd}
        ).build()

    def test_header_contains_tool_name(self):
        payload = self._build("Write", {"file_path": "/f.swift"})
        header = payload["blocks"][0]["text"]["text"]
        self.assertIn("Write", header)
        self.assertIn(":pencil2:", header)

    def test_context_has_project_and_summary(self):
        payload = self._build("Write", {"file_path": "/src/Foo.swift"})
        context = payload["blocks"][1]["elements"]
        texts = [e["text"] for e in context]
        self.assertTrue(any("proj" in t for t in texts))
        self.assertTrue(any("Foo.swift" in t for t in texts))

    def test_bash_command_in_context(self):
        payload = self._build("Bash", {"command": "git push"})
        context = payload["blocks"][1]["elements"]
        self.assertTrue(any("git push" in e["text"] for e in context))

    def test_no_context_when_no_cwd_and_no_summary(self):
        payload = self._build("Read", {}, cwd="")
        self.assertEqual(len(payload["blocks"]), 1)

    def test_unknown_tool_uses_default_icon(self):
        payload = self._build("Task", {})
        self.assertIn(":key:", payload["blocks"][0]["text"]["text"])

    def test_text_field_contains_tool_name(self):
        payload = self._build("Bash", {"command": "ls"})
        self.assertIn("Bash", payload["text"])


class TestSlackPermissionNotifier(unittest.TestCase):
    def _make(self, enabled=True):
        config = EnvConfigReader(env=FakeEnv(
            {"CLAUDE_SLACK_NOTIFY": "https://x"} if enabled else {}
        ))
        self._sender = RecordingHttpSender()
        return SlackPermissionNotifier(
            config=config,
            dispatcher_factory=lambda url: WebhookDispatcher(url, http_sender=self._sender),
        )

    def test_should_handle_when_enabled(self):
        self.assertTrue(self._make().should_handle({}))

    def test_should_not_handle_when_disabled(self):
        self.assertFalse(self._make(enabled=False).should_handle({}))

    def test_handle_sends_payload(self):
        n = self._make()
        n.handle({"tool_name": "Write", "tool_input": {"file_path": "/f.py"}, "cwd": "/p"})
        self.assertEqual(len(self._sender.calls), 1)

    def test_gate_skips_handle_when_disabled(self):
        from on_stop import OnStopGate
        n = self._make(enabled=False)
        OnStopGate(handlers=[n]).run({"tool_name": "Bash", "tool_input": {"command": "ls"}})
        self.assertEqual(len(self._sender.calls), 0)


if __name__ == "__main__":
    unittest.main()
