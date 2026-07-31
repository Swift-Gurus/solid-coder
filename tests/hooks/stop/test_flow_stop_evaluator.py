"""
solid-name: test_flow_stop_evaluator
solid-category: unit-test
solid-description: Validates that stop evaluation produces correct allow/deny decisions with reason preservation and executes exactly once per event.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from stop_handler_doubles import StubGate
from flow_transition_handler import FlowStopEvaluator


class TestFlowStopEvaluator(unittest.TestCase):
    def test_allow_result_produces_allow_decision(self):
        gate = StubGate({"allow": True})

        decision = FlowStopEvaluator(gate).evaluate_stop({})

        self.assertTrue(decision.allow)
        self.assertEqual(gate.evaluate_calls, 1)

    def test_deny_result_carries_reason_through(self):
        gate = StubGate({"allow": False, "reason": "Flow 'x' has pending step(s) ['a']."})

        decision = FlowStopEvaluator(gate).evaluate_stop({})

        self.assertFalse(decision.allow)
        self.assertEqual(decision.reason, "Flow 'x' has pending step(s) ['a'].")

    def test_evaluate_called_exactly_once_per_stop_event(self):
        """Critical for the 3-attempt exhaustion counter: a double-call would corrupt it."""
        gate = StubGate({"allow": False, "reason": "pending"})

        FlowStopEvaluator(gate).evaluate_stop({})

        self.assertEqual(gate.evaluate_calls, 1)


if __name__ == "__main__":
    unittest.main()
