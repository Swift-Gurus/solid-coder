"""Tests for slack_notify.py"""

import sys
import unittest
from pathlib import Path

HOOKS_DIR = str(Path(__file__).resolve().parents[1])
if HOOKS_DIR not in sys.path:
    sys.path.insert(0, HOOKS_DIR)

from slack_notify import (
    AssistantTextReader,
    EnvConfigReader,
    ModeClassifier,
    SkillCallsReader,
    SlackPayloadBuilder,
    SlackStopNotifier,
    TranscriptReader,
    WebhookDispatcher,
    _normalize_content_text,
)


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------

class FakeEnv:
    def __init__(self, values):
        self._values = values

    def get(self, key, default=""):
        return self._values.get(key, default)


class FakeLineReader:
    def __init__(self, lines):
        self._lines = lines

    def read_lines(self, path):
        return self._lines


class FakePathNamer:
    def __init__(self, result):
        self._result = result

    def name(self, path):
        return self._result


class RecordingHttpSender:
    def __init__(self):
        self.calls = []

    def send(self, url, data, headers, timeout):
        self.calls.append((url, data, headers, timeout))
        return b""


class FailingHttpSender:
    def send(self, url, data, headers, timeout):
        raise OSError("network down")


def _assistant_text_line(text):
    import json
    return json.dumps({
        "type": "assistant",
        "message": {"content": [{"type": "text", "text": text}]},
    })


def _skill_line(skill):
    import json
    return json.dumps({
        "type": "assistant",
        "message": {"content": [
            {"type": "tool_use", "name": "Skill", "input": {"skill": skill}}
        ]},
    })


def _command_message_line(command, args=""):
    import json
    text = f"<command-message>{command}</command-message>\n<command-name>/{command}</command-name>"
    if args:
        text += f"\n<command-args>{args}</command-args>"
    return json.dumps({
        "type": "user",
        "message": {"content": [{"type": "text", "text": text}]},
    })


def _plain_user_line(text):
    import json
    return json.dumps({
        "type": "user",
        "message": {"content": [{"type": "text", "text": text}]},
    })


# ---------------------------------------------------------------------------
# _normalize_content_text
# ---------------------------------------------------------------------------

class TestNormalizeContentText(unittest.TestCase):
    def test_string_passthrough(self):
        self.assertEqual(_normalize_content_text("hello"), "hello")

    def test_list_with_text_block(self):
        self.assertEqual(_normalize_content_text([{"type": "text", "text": "hi"}]), "hi")

    def test_empty_list(self):
        self.assertEqual(_normalize_content_text([]), "")

    def test_none_returns_empty(self):
        self.assertEqual(_normalize_content_text(None), "")


# ---------------------------------------------------------------------------
# EnvConfigReader
# ---------------------------------------------------------------------------

class TestEnvConfigReader(unittest.TestCase):
    def test_is_enabled_when_url_present(self):
        r = EnvConfigReader(env=FakeEnv({"CLAUDE_SLACK_NOTIFY": "https://hooks.slack.com/x"}))
        self.assertTrue(r.is_enabled())

    def test_not_enabled_when_empty(self):
        r = EnvConfigReader(env=FakeEnv({}))
        self.assertFalse(r.is_enabled())

    def test_webhook_url_strips_whitespace(self):
        r = EnvConfigReader(env=FakeEnv({"CLAUDE_SLACK_NOTIFY": "  https://x.com  "}))
        self.assertEqual(r.webhook_url(), "https://x.com")


# ---------------------------------------------------------------------------
# AssistantTextReader
# ---------------------------------------------------------------------------

class TestAssistantTextReader(unittest.TestCase):
    def _make(self, lines):
        return AssistantTextReader("ignored", FakeLineReader(lines))

    def test_returns_last_text_block(self):
        r = self._make([_assistant_text_line("first"), _assistant_text_line("second")])
        self.assertEqual(r.last_assistant_text(), "second")

    def test_empty_transcript_returns_empty(self):
        self.assertEqual(self._make([]).last_assistant_text(), "")

    def test_skips_empty_text_blocks(self):
        import json
        lines = [
            _assistant_text_line("hello"),
            json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "  "}]}}),
        ]
        self.assertEqual(self._make(lines).last_assistant_text(), "hello")

    def test_ignores_malformed_lines(self):
        self.assertEqual(self._make(["not json", _assistant_text_line("good")]).last_assistant_text(), "good")

    def test_ignores_non_assistant_entries(self):
        import json
        lines = [json.dumps({"type": "human", "message": {"content": [{"type": "text", "text": "msg"}]}})]
        self.assertEqual(self._make(lines).last_assistant_text(), "")


# ---------------------------------------------------------------------------
# SkillCallsReader
# ---------------------------------------------------------------------------

class TestSkillCallsReaderCommandMessage(unittest.TestCase):
    def _make(self, lines):
        return SkillCallsReader("ignored", FakeLineReader(lines))

    def test_reads_command_message_from_first_user_line(self):
        r = self._make([_command_message_line("solid-coder:implement", "spec-015")])
        self.assertEqual(r.skill_calls(), ["solid-coder:implement"])

    def test_command_message_takes_precedence_over_tool_use(self):
        r = self._make([
            _command_message_line("solid-coder:review"),
            _skill_line("solid-coder:implement"),
        ])
        self.assertEqual(r.skill_calls(), ["solid-coder:review"])

    def test_plain_user_message_falls_through_to_tool_use(self):
        r = self._make([_plain_user_line("hello"), _skill_line("solid-coder:refactor")])
        self.assertEqual(r.skill_calls(), ["solid-coder:refactor"])

    def test_no_command_and_no_tool_use_returns_empty(self):
        r = self._make([_plain_user_line("hello")])
        self.assertEqual(r.skill_calls(), [])


class TestSkillCallsReaderToolUse(unittest.TestCase):
    def _make(self, lines):
        return SkillCallsReader("ignored", FakeLineReader(lines))

    def test_collects_skill_names_from_tool_use(self):
        lines = [_skill_line("solid-coder:review"), _skill_line("solid-coder:implement")]
        self.assertEqual(self._make(lines).skill_calls(), ["solid-coder:review", "solid-coder:implement"])

    def test_ignores_non_skill_tool_calls(self):
        import json
        lines = [json.dumps({
            "type": "assistant",
            "message": {"content": [{"type": "tool_use", "name": "Bash", "input": {"command": "ls"}}]},
        })]
        self.assertEqual(self._make(lines).skill_calls(), [])

    def test_empty_transcript_returns_empty_list(self):
        self.assertEqual(self._make([]).skill_calls(), [])


# ---------------------------------------------------------------------------
# ModeClassifier
# ---------------------------------------------------------------------------

class TestModeClassifier(unittest.TestCase):
    def setUp(self):
        self.c = ModeClassifier()

    def test_review(self):
        self.assertEqual(self.c.classify(["solid-coder:review"]), "review")

    def test_implement(self):
        self.assertEqual(self.c.classify(["solid-coder:implement"]), "implement")

    def test_refactor(self):
        self.assertEqual(self.c.classify(["solid-coder:refactor"]), "refactor")

    def test_command_with_args_still_matches(self):
        # command-message may include args: "solid-coder:refactor --iterations 1"
        self.assertEqual(self.c.classify(["solid-coder:refactor --iterations 1"]), "refactor")

    def test_vibe_when_no_recognized_skill(self):
        self.assertEqual(self.c.classify(["solid-coder:code"]), "vibe")

    def test_vibe_when_empty(self):
        self.assertEqual(self.c.classify([]), "vibe")

    def test_first_match_wins(self):
        self.assertEqual(
            self.c.classify(["solid-coder:review", "solid-coder:implement"]),
            "review",
        )


# ---------------------------------------------------------------------------
# SlackPayloadBuilder
# ---------------------------------------------------------------------------

class TestSlackPayloadBuilder(unittest.TestCase):
    def _build(self, mode="vibe", last_message="", cwd="/projects/myapp"):
        event = {"cwd": cwd}
        namer = FakePathNamer("myapp")
        return SlackPayloadBuilder(event, mode=mode, last_message=last_message, path_namer=namer).build()

    def test_icon_matches_mode(self):
        cases = [
            ("review", ":mag:"),
            ("implement", ":hammer_and_wrench:"),
            ("refactor", ":recycle:"),
            ("vibe", "🪄"),
        ]
        for mode, expected_icon in cases:
            with self.subTest(mode=mode):
                payload = self._build(mode=mode)
                self.assertNotIn("icon_emoji", payload)
                self.assertIn(expected_icon, payload["blocks"][0]["text"]["text"])

    def test_context_block_contains_project_and_path(self):
        payload = self._build()
        context_block = next(b for b in payload["blocks"] if b.get("type") == "context")
        texts = [e["text"] for e in context_block["elements"]]
        self.assertTrue(any("myapp" in t for t in texts))
        self.assertTrue(any("/projects/myapp" in t for t in texts))

    def test_last_message_appended_as_section(self):
        payload = self._build(last_message="All done!")
        section_texts = [
            b["text"]["text"] for b in payload["blocks"] if b.get("type") == "section"
        ]
        self.assertTrue(any("All done!" in t for t in section_texts))

    def test_last_message_truncated_at_500_chars(self):
        long_msg = "x" * 600
        payload = self._build(last_message=long_msg)
        section_texts = [
            b["text"]["text"] for b in payload["blocks"] if b.get("type") == "section"
        ]
        self.assertLessEqual(len(section_texts[-1]), 502)
        self.assertTrue(section_texts[-1].endswith("…"))

    def test_divider_present_when_last_message_set(self):
        types = [b["type"] for b in self._build(last_message="hello")["blocks"]]
        self.assertIn("divider", types)

    def test_no_divider_when_no_last_message(self):
        types = [b["type"] for b in self._build(last_message="")["blocks"]]
        self.assertNotIn("divider", types)

    def test_no_context_when_cwd_empty(self):
        payload = SlackPayloadBuilder({"cwd": ""}, path_namer=FakePathNamer("")).build()
        types = [b["type"] for b in payload["blocks"]]
        self.assertNotIn("context", types)


# ---------------------------------------------------------------------------
# WebhookDispatcher
# ---------------------------------------------------------------------------

class TestWebhookDispatcher(unittest.TestCase):
    def test_posts_json_to_url(self):
        import json as _json
        sender = RecordingHttpSender()
        d = WebhookDispatcher("https://example.com/hook", http_sender=sender)
        d.send({"text": "hello"})
        self.assertEqual(len(sender.calls), 1)
        url, data, headers, timeout = sender.calls[0]
        self.assertEqual(url, "https://example.com/hook")
        self.assertEqual(_json.loads(data)["text"], "hello")
        self.assertEqual(headers["Content-Type"], "application/json")

    def test_errors_do_not_raise(self):
        WebhookDispatcher("https://x.com", http_sender=FailingHttpSender()).send({"text": "hi"})


# ---------------------------------------------------------------------------
# SlackStopNotifier integration
# ---------------------------------------------------------------------------

class TestSlackStopNotifier(unittest.TestCase):
    def _make_notifier(self, webhook_url="https://hook.slack.com/x", command=None, last_text="done"):
        config = EnvConfigReader(env=FakeEnv({"CLAUDE_SLACK_NOTIFY": webhook_url}))

        lines = []
        if command:
            lines.append(_command_message_line(command))
        if last_text:
            lines.append(_assistant_text_line(last_text))

        def reader_factory(path):
            return TranscriptReader(
                path,
                skills_reader=SkillCallsReader(path, FakeLineReader(lines)),
                text_reader=AssistantTextReader(path, FakeLineReader(lines)),
            )

        self._sender = RecordingHttpSender()

        def dispatcher_factory(url):
            return WebhookDispatcher(url, http_sender=self._sender)

        return SlackStopNotifier(
            config=config,
            transcript_reader_factory=reader_factory,
            dispatcher_factory=dispatcher_factory,
        )

    def _sent_payload(self):
        import json as _json
        _, data, _, _ = self._sender.calls[0]
        return _json.loads(data)

    def test_should_handle_when_enabled(self):
        self.assertTrue(self._make_notifier().should_handle({}))

    def test_should_not_handle_when_disabled(self):
        self.assertFalse(self._make_notifier(webhook_url="").should_handle({}))

    def test_payload_contains_last_message(self):
        n = self._make_notifier(last_text="Task complete")
        n.handle({"cwd": "/p/proj", "transcript_path": "fake.jsonl"})
        texts = [b["text"]["text"] for b in self._sent_payload()["blocks"] if b.get("type") == "section"]
        self.assertTrue(any("Task complete" in t for t in texts))

    def test_implement_command_sets_implement_icon(self):
        n = self._make_notifier(command="solid-coder:implement")
        n.handle({"cwd": "/p/proj", "transcript_path": "fake.jsonl"})
        header = self._sent_payload()["blocks"][0]["text"]["text"]
        self.assertIn(":hammer_and_wrench:", header)

    def test_review_command_sets_review_icon(self):
        n = self._make_notifier(command="solid-coder:review")
        n.handle({"cwd": "/p/proj", "transcript_path": "fake.jsonl"})
        header = self._sent_payload()["blocks"][0]["text"]["text"]
        self.assertIn(":mag:", header)

    def test_no_transcript_path_defaults_to_vibe(self):
        n = self._make_notifier()
        n.handle({"cwd": "/p/proj"})
        header = self._sent_payload()["blocks"][0]["text"]["text"]
        self.assertIn("🪄", header)


if __name__ == "__main__":
    unittest.main()
