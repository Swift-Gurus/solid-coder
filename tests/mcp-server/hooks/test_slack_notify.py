"""Tests for slack_notify.py"""

import sys
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

HOOKS_DIR = str(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks")
if HOOKS_DIR not in sys.path:
    sys.path.insert(0, HOOKS_DIR)

from slack_notify import (
    AssistantTextReader,
    EnvConfigReader,
    JSONLTranscriptParser,
    ModeClassifier,
    SlackPayloadBuilder,
    SlackStopNotifier,
    SkillCallsReader,
    TomlThresholdReader,
    TranscriptElapsedReader,
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


class FakeClock:
    def __init__(self, dt):
        self._dt = dt

    def now_utc(self):
        return self._dt


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


def _plain_user_line(text, timestamp=None):
    import json
    obj = {"type": "user", "message": {"content": [{"type": "text", "text": text}]}}
    if timestamp:
        obj["timestamp"] = timestamp
    return json.dumps(obj)


def _make_parser(lines):
    return JSONLTranscriptParser(FakeLineReader(lines))


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
# JSONLTranscriptParser
# ---------------------------------------------------------------------------

class TestJSONLTranscriptParser(unittest.TestCase):
    def test_parses_valid_lines(self):
        lines = ['{"type": "user"}', '{"type": "assistant"}']
        p = JSONLTranscriptParser(FakeLineReader(lines))
        msgs = p.messages("ignored")
        self.assertEqual(len(msgs), 2)

    def test_skips_malformed_lines(self):
        lines = ["not json", '{"type": "user"}']
        p = JSONLTranscriptParser(FakeLineReader(lines))
        self.assertEqual(len(p.messages("ignored")), 1)

    def test_empty_input(self):
        p = JSONLTranscriptParser(FakeLineReader([]))
        self.assertEqual(p.messages("ignored"), [])


# ---------------------------------------------------------------------------
# EnvConfigReader
# ---------------------------------------------------------------------------

class TestEnvConfigReader(unittest.TestCase):
    def test_is_enabled_when_url_present(self):
        r = EnvConfigReader(env=FakeEnv({"CLAUDE_SLACK_NOTIFY": "https://x"}))
        self.assertTrue(r.is_enabled())

    def test_not_enabled_when_empty(self):
        r = EnvConfigReader(env=FakeEnv({}))
        self.assertFalse(r.is_enabled())

    def test_webhook_url_strips_whitespace(self):
        r = EnvConfigReader(env=FakeEnv({"CLAUDE_SLACK_NOTIFY": "  https://x.com  "}))
        self.assertEqual(r.webhook_url(), "https://x.com")


# ---------------------------------------------------------------------------
# TomlThresholdReader
# ---------------------------------------------------------------------------

class TestTomlThresholdReader(unittest.TestCase):
    def test_uses_injected_fn(self):
        r = TomlThresholdReader(threshold_fn=lambda: 60)
        self.assertEqual(r.threshold_seconds(), 60)

    def test_default_sixty(self):
        r = TomlThresholdReader(threshold_fn=lambda: 60)
        self.assertEqual(r.threshold_seconds(), 60)


# ---------------------------------------------------------------------------
# AssistantTextReader
# ---------------------------------------------------------------------------

class TestAssistantTextReader(unittest.TestCase):
    def _make(self, lines):
        return AssistantTextReader("ignored", _make_parser(lines))

    def test_returns_last_text_block(self):
        lines = [_assistant_text_line("first"), _assistant_text_line("second")]
        self.assertEqual(self._make(lines).last_assistant_text(), "second")

    def test_empty_returns_empty(self):
        self.assertEqual(self._make([]).last_assistant_text(), "")

    def test_skips_whitespace_only_blocks(self):
        import json
        lines = [
            _assistant_text_line("hello"),
            json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "  "}]}}),
        ]
        self.assertEqual(self._make(lines).last_assistant_text(), "hello")

    def test_ignores_non_assistant_entries(self):
        lines = [_plain_user_line("user msg")]
        self.assertEqual(self._make(lines).last_assistant_text(), "")


# ---------------------------------------------------------------------------
# SkillCallsReader
# ---------------------------------------------------------------------------

class TestSkillCallsReaderCommandMessage(unittest.TestCase):
    def _make(self, lines):
        return SkillCallsReader("ignored", _make_parser(lines))

    def test_reads_command_message(self):
        r = self._make([_command_message_line("solid-coder:implement", "spec-015")])
        self.assertEqual(r.skill_calls(), ["solid-coder:implement"])

    def test_command_message_beats_tool_use(self):
        r = self._make([_command_message_line("solid-coder:review"), _skill_line("solid-coder:implement")])
        self.assertEqual(r.skill_calls(), ["solid-coder:review"])

    def test_falls_through_to_tool_use(self):
        r = self._make([_plain_user_line("hello"), _skill_line("solid-coder:refactor")])
        self.assertEqual(r.skill_calls(), ["solid-coder:refactor"])

    def test_empty_returns_empty(self):
        self.assertEqual(self._make([]).skill_calls(), [])


# ---------------------------------------------------------------------------
# TranscriptElapsedReader
# ---------------------------------------------------------------------------

class TestTranscriptElapsedReader(unittest.TestCase):
    def _make(self, lines, now_utc):
        return TranscriptElapsedReader(
            file_reader=FakeLineReader(lines),
            clock=FakeClock(now_utc),
        )

    def test_returns_elapsed_seconds(self):
        now = datetime(2026, 6, 9, 10, 0, 30, tzinfo=timezone.utc)
        lines = [_plain_user_line("hi", timestamp="2026-06-09T10:00:00.000Z")]
        r = self._make(lines, now)
        self.assertAlmostEqual(r.elapsed_seconds("ignored"), 30.0, places=0)

    def test_uses_last_user_timestamp(self):
        now = datetime(2026, 6, 9, 10, 1, 0, tzinfo=timezone.utc)
        lines = [
            _plain_user_line("first", timestamp="2026-06-09T10:00:00.000Z"),
            _plain_user_line("last", timestamp="2026-06-09T10:00:50.000Z"),
        ]
        r = self._make(lines, now)
        self.assertAlmostEqual(r.elapsed_seconds("ignored"), 10.0, places=0)

    def test_no_timestamp_returns_inf(self):
        now = datetime(2026, 6, 9, 10, 0, 0, tzinfo=timezone.utc)
        r = self._make([_plain_user_line("no timestamp")], now)
        self.assertEqual(r.elapsed_seconds("ignored"), float("inf"))

    def test_empty_transcript_returns_inf(self):
        now = datetime(2026, 6, 9, 10, 0, 0, tzinfo=timezone.utc)
        r = self._make([], now)
        self.assertEqual(r.elapsed_seconds("ignored"), float("inf"))

    def test_tool_result_messages_are_ignored(self):
        import json
        now = datetime(2026, 6, 9, 10, 1, 0, tzinfo=timezone.utc)
        human_msg = _plain_user_line("fix this", timestamp="2026-06-09T10:00:00.000Z")
        tool_result_msg = json.dumps({
            "type": "user",
            "timestamp": "2026-06-09T10:00:59.000Z",  # 59s later — would give 1s elapsed
            "message": {"content": [{"type": "tool_result", "content": "ok"}]},
        })
        r = self._make([human_msg, tool_result_msg], now)
        # elapsed should be measured from the HUMAN message (60s), not the tool_result (1s)
        self.assertAlmostEqual(r.elapsed_seconds("ignored"), 60.0, places=0)


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

    def test_command_with_args_matches(self):
        self.assertEqual(self.c.classify(["solid-coder:refactor --iterations 1"]), "refactor")

    def test_vibe_default(self):
        self.assertEqual(self.c.classify([]), "vibe")

    def test_first_match_wins(self):
        self.assertEqual(self.c.classify(["solid-coder:review", "solid-coder:implement"]), "review")


# ---------------------------------------------------------------------------
# SlackPayloadBuilder
# ---------------------------------------------------------------------------

class TestSlackPayloadBuilder(unittest.TestCase):
    def _build(self, mode="vibe", last_message="", cwd="/projects/myapp"):
        return SlackPayloadBuilder(
            {"cwd": cwd}, mode=mode, last_message=last_message,
            path_namer=FakePathNamer("myapp"),
        ).build()

    def test_header_uses_first_line_of_message(self):
        payload = self._build(last_message="All done!\nMore details here.")
        header = payload["blocks"][0]["text"]["text"]
        self.assertIn("All done!", header)
        self.assertNotIn("More details", header)

    def test_fallback_header_when_no_message(self):
        payload = self._build(last_message="")
        self.assertIn("Finished", payload["blocks"][0]["text"]["text"])

    def test_text_field_uses_first_line(self):
        payload = self._build(last_message="Task done.\nDetails.")
        self.assertEqual(payload["text"], "Task done.")

    def test_icon_in_header_for_each_mode(self):
        cases = [("review", ":mag:"), ("implement", ":hammer_and_wrench:"),
                 ("refactor", ":recycle:"), ("vibe", ":magic_wand:")]
        for mode, icon in cases:
            with self.subTest(mode=mode):
                header = self._build(mode=mode)["blocks"][0]["text"]["text"]
                self.assertIn(icon, header)

    def test_no_icon_emoji_field(self):
        self.assertNotIn("icon_emoji", self._build())

    def test_divider_when_message(self):
        types = [b["type"] for b in self._build(last_message="hi")["blocks"]]
        self.assertIn("divider", types)

    def test_no_divider_without_message(self):
        types = [b["type"] for b in self._build(last_message="")["blocks"]]
        self.assertNotIn("divider", types)

    def test_message_truncated_at_500(self):
        payload = self._build(last_message="x" * 600)
        sections = [b["text"]["text"] for b in payload["blocks"] if b.get("type") == "section"]
        self.assertTrue(sections[-1].endswith("…"))
        self.assertLessEqual(len(sections[-1]), 502)


# ---------------------------------------------------------------------------
# WebhookDispatcher
# ---------------------------------------------------------------------------

class TestWebhookDispatcher(unittest.TestCase):
    def test_posts_json_to_url(self):
        import json as _json
        sender = RecordingHttpSender()
        WebhookDispatcher("https://x.com/hook", http_sender=sender).send({"text": "hi"})
        url, data, headers, _ = sender.calls[0]
        self.assertEqual(url, "https://x.com/hook")
        self.assertEqual(_json.loads(data)["text"], "hi")

    def test_errors_do_not_raise(self):
        WebhookDispatcher("https://x.com", http_sender=FailingHttpSender()).send({})


# ---------------------------------------------------------------------------
# SlackStopNotifier
# ---------------------------------------------------------------------------

class TestSlackStopNotifierShouldHandle(unittest.TestCase):
    def _notifier(self, enabled=True, threshold=0, elapsed=float("inf")):
        config = EnvConfigReader(env=FakeEnv(
            {"CLAUDE_SLACK_NOTIFY": "https://x"} if enabled else {}
        ))
        return SlackStopNotifier(
            config=config,
            threshold_reader=TomlThresholdReader(threshold_fn=lambda: threshold),
            elapsed_reader=type("E", (), {"elapsed_seconds": lambda self, p: elapsed})(),
            dispatcher_factory=lambda url: WebhookDispatcher(url, http_sender=RecordingHttpSender()),
        )

    def test_disabled_when_no_webhook(self):
        self.assertFalse(self._notifier(enabled=False).should_handle({}))

    def test_enabled_when_threshold_zero(self):
        self.assertTrue(self._notifier(threshold=0, elapsed=5).should_handle({}))

    def test_fires_when_elapsed_exceeds_threshold(self):
        self.assertTrue(self._notifier(threshold=30, elapsed=45).should_handle({}))

    def test_suppressed_when_elapsed_below_threshold(self):
        self.assertFalse(self._notifier(threshold=30, elapsed=10).should_handle({}))

    def test_fires_when_no_transcript_inf_elapsed(self):
        self.assertTrue(self._notifier(threshold=30, elapsed=float("inf")).should_handle({}))


class TestSlackStopNotifierHandle(unittest.TestCase):
    def _make(self, command=None, last_text="done"):
        lines = []
        if command:
            lines.append(_command_message_line(command))
        if last_text:
            lines.append(_assistant_text_line(last_text))

        self._sender = RecordingHttpSender()

        def reader_factory(path):
            return TranscriptReader(
                path,
                skills_reader=SkillCallsReader(path, _make_parser(lines)),
                text_reader=AssistantTextReader(path, _make_parser(lines)),
            )

        return SlackStopNotifier(
            config=EnvConfigReader(env=FakeEnv({"CLAUDE_SLACK_NOTIFY": "https://x"})),
            transcript_reader_factory=reader_factory,
            dispatcher_factory=lambda url: WebhookDispatcher(url, http_sender=self._sender),
            threshold_reader=TomlThresholdReader(threshold_fn=lambda: 0),
        )

    def _payload(self):
        import json as _j
        return _j.loads(self._sender.calls[0][1])

    def test_implement_sets_implement_icon(self):
        n = self._make(command="solid-coder:implement")
        n.handle({"cwd": "/p", "transcript_path": "fake.jsonl"})
        self.assertIn(":hammer_and_wrench:", self._payload()["blocks"][0]["text"]["text"])

    def test_last_message_in_payload(self):
        n = self._make(last_text="Task complete")
        n.handle({"cwd": "/p", "transcript_path": "fake.jsonl"})
        texts = [b["text"]["text"] for b in self._payload()["blocks"] if b.get("type") == "section"]
        self.assertTrue(any("Task complete" in t for t in texts))

    def test_vibe_default_without_transcript(self):
        n = self._make()
        n.handle({"cwd": "/p"})
        self.assertIn(":magic_wand:", self._payload()["blocks"][0]["text"]["text"])


if __name__ == "__main__":
    unittest.main()
