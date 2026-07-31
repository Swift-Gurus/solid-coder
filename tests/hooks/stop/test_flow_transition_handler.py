"""
solid-name: test_flow_transition_handler
solid-category: unit-test
solid-description: Tests flow transition authorization decisions based on stop conditions.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from stop_handler_doubles import StubGate
from flow_transition_handler import FlowStopEvaluator, FlowTransitionHandler


class TestFlowTransitionHandler(unittest.TestCase):
    def test_should_handle_false_when_stop_hook_active(self):
        handler = FlowTransitionHandler(evaluator=FlowStopEvaluator(StubGate({"allow": False})))

        self.assertFalse(handler.should_handle({"stop_hook_active": True}))

    def test_should_handle_true_on_fresh_attempt(self):
        handler = FlowTransitionHandler(evaluator=FlowStopEvaluator(StubGate({"allow": True})))

        self.assertTrue(handler.should_handle({}))

    def test_handle_delegates_to_evaluator(self):
        gate = StubGate({"allow": False, "reason": "blocked"})
        handler = FlowTransitionHandler(evaluator=FlowStopEvaluator(gate))

        decision = handler.handle({})

        self.assertFalse(decision.allow)
        self.assertEqual(decision.reason, "blocked")
        self.assertEqual(gate.evaluate_calls, 1)


if __name__ == "__main__":
    unittest.main()
