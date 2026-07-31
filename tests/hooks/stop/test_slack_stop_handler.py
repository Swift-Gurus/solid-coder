"""
solid-name: test_slack_stop_handler
solid-category: unit-test
solid-description: Validates SlackStopHandler's notification management and event handling.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from stop_handler_doubles import StubNotifier
from slack_stop_handler import SlackStopHandler


class TestSlackStopHandler(unittest.TestCase):
    def test_should_handle_delegates_to_notifier_when_no_session_type_set(self):
        notifier = StubNotifier(should=True)
        handler = SlackStopHandler(notifier, session_type_fn=lambda: "")

        self.assertTrue(handler.should_handle({}))

    def test_should_handle_false_when_notifier_declines(self):
        notifier = StubNotifier(should=False)
        handler = SlackStopHandler(notifier, session_type_fn=lambda: "")

        self.assertFalse(handler.should_handle({}))

    def test_should_handle_false_during_internal_session_even_if_notifier_would_accept(self):
        notifier = StubNotifier(should=True)
        handler = SlackStopHandler(notifier, session_type_fn=lambda: "health-check")

        self.assertFalse(handler.should_handle({}))

    def test_handle_forwards_event_to_notifier_and_always_allows(self):
        notifier = StubNotifier(should=True)
        handler = SlackStopHandler(notifier, session_type_fn=lambda: "")
        event = {"session_id": "abc"}

        decision = handler.handle(event)

        self.assertTrue(decision.allow)
        self.assertIsNone(decision.reason)
        self.assertEqual(notifier.handled_events, [event])


if __name__ == "__main__":
    unittest.main()
