"""
solid-name: test_hook_decision_aggregator
solid-category: unit-test
solid-description: Validates decision aggregation with denial precedence and context consolidation.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from hook_decision import HookDecision
from hook_decision_aggregator import HookDecisionAggregator


class TestHookDecisionAggregator(unittest.TestCase):
    def setUp(self):
        self.aggregator = HookDecisionAggregator()

    def test_empty_list_allows(self):
        result = self.aggregator.aggregate([])

        self.assertTrue(result.allow)
        self.assertIsNone(result.reason)
        self.assertIsNone(result.additional_context)

    def test_all_allow_produces_allow(self):
        result = self.aggregator.aggregate([HookDecision(allow=True), HookDecision(allow=True)])

        self.assertTrue(result.allow)
        self.assertIsNone(result.reason)

    def test_single_denial_denies(self):
        result = self.aggregator.aggregate([HookDecision(allow=True), HookDecision(allow=False, reason="blocked")])

        self.assertFalse(result.allow)
        self.assertEqual(result.reason, "blocked")

    def test_multiple_denials_concatenate_reasons_from_all_of_them(self):
        result = self.aggregator.aggregate([
            HookDecision(allow=False, reason="reason one"),
            HookDecision(allow=True),
            HookDecision(allow=False, reason="reason two"),
        ])

        self.assertFalse(result.allow)
        self.assertEqual(result.reason, "reason one\nreason two")

    def test_additional_context_aggregated_regardless_of_allow_or_deny(self):
        result = self.aggregator.aggregate([
            HookDecision(allow=True, additional_context="reminder one"),
            HookDecision(allow=False, reason="blocked", additional_context="reminder two"),
        ])

        self.assertFalse(result.allow)
        self.assertEqual(result.additional_context, "reminder one\nreminder two")

    def test_additional_context_none_when_no_decision_provides_one(self):
        result = self.aggregator.aggregate([HookDecision(allow=True), HookDecision(allow=False, reason="x")])

        self.assertIsNone(result.additional_context)


if __name__ == "__main__":
    unittest.main()
