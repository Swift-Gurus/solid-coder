"""
solid-name: test_safe_handler_runner
solid-category: unit-test
solid-description: Verifies that handler execution failures result in fail-open allow decisions and error logging.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from hook_dispatch_doubles import RecordingLogger, StubHandler
from hook_decision import HookDecision
from safe_handler_runner import SafeHandlerRunner


class TestSafeHandlerRunner(unittest.TestCase):
    def test_returns_handler_decision_when_no_exception(self):
        decision = HookDecision(allow=False, reason="blocked")
        logger = RecordingLogger()
        runner = SafeHandlerRunner(logger=logger)

        result = runner.run(StubHandler(decision=decision), {})

        self.assertIs(result, decision)
        self.assertEqual(logger.messages, [])

    def test_raising_handler_fails_open_and_logs(self):
        logger = RecordingLogger()
        runner = SafeHandlerRunner(logger=logger)

        result = runner.run(StubHandler(exc=RuntimeError("boom")), {})

        self.assertTrue(result.allow)
        self.assertIsNone(result.reason)
        self.assertEqual(len(logger.messages), 1)
        self.assertIn("boom", logger.messages[0])


if __name__ == "__main__":
    unittest.main()
