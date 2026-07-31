"""
solid-name: test_flow_stop_applicability_checker
solid-category: unit-test
solid-description: Verifies that stop operation applicability is correctly prevented when concurrent stops are attempted.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks"))

from flow_transition_handler import FlowStopApplicabilityChecker


class TestFlowStopApplicabilityChecker(unittest.TestCase):
    def test_does_not_apply_when_stop_hook_already_active(self):
        self.assertFalse(FlowStopApplicabilityChecker().applies({"stop_hook_active": True}))

    def test_applies_on_a_fresh_stop_attempt(self):
        self.assertTrue(FlowStopApplicabilityChecker().applies({}))


if __name__ == "__main__":
    unittest.main()
