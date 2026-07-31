"""
solid-name: test_on_stop
solid-category: unit-test
solid-description: Verifies on_stop.main() correctly routes HookDecision outcomes to the responder.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from hook_decision import HookDecision
from on_stop import main
from stop_handler_doubles import RecordingResponder, StubDispatcher, StubReader


class TestOnStopMain(unittest.TestCase):
    def test_allow_decision_calls_responder_allow(self):
        dispatcher = StubDispatcher(HookDecision(allow=True))
        responder = RecordingResponder()

        main(reader=StubReader({"session_id": "abc"}), dispatcher=dispatcher, responder=responder)

        self.assertEqual(responder.allow_calls, [""])
        self.assertEqual(responder.block_calls, [])
        self.assertEqual(dispatcher.dispatched_events, [{"session_id": "abc"}])

    def test_allow_decision_with_additional_context_forwards_it(self):
        dispatcher = StubDispatcher(HookDecision(allow=True, additional_context="reminder"))
        responder = RecordingResponder()

        main(reader=StubReader({}), dispatcher=dispatcher, responder=responder)

        self.assertEqual(responder.allow_calls, ["reminder"])

    def test_deny_decision_calls_responder_block_with_reason_and_context(self):
        dispatcher = StubDispatcher(HookDecision(allow=False, reason="blocked", additional_context="ctx"))
        responder = RecordingResponder()

        main(reader=StubReader({}), dispatcher=dispatcher, responder=responder)

        self.assertEqual(responder.block_calls, [("blocked", "ctx")])
        self.assertEqual(responder.allow_calls, [])

    def test_deny_decision_without_reason_falls_back_to_default(self):
        dispatcher = StubDispatcher(HookDecision(allow=False))
        responder = RecordingResponder()

        main(reader=StubReader({}), dispatcher=dispatcher, responder=responder)

        self.assertEqual(responder.block_calls, [("Blocked.", "")])


if __name__ == "__main__":
    unittest.main()
