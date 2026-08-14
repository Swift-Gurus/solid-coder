"""Verifies partial merging of metric configuration overrides."""

import unittest
from pathlib import Path

from config_override_test_context import ConfigOverrideTestContext


_CONTEXT = ConfigOverrideTestContext(Path(__file__).resolve().parents[3] / "references")


"""
solid-name: PartialConfigMergeTests
solid-category: unit-test
solid-description: Verifies one variable override preserves sibling metric configuration.
"""
class PartialConfigMergeTests(unittest.TestCase):
    def test_partial_merge_preserves_sibling_variable(self):
        _, rule_path = _CONTEXT.metrics[("OCP", "OCP-2", "untestable_dependencies")]
        config = {"OCP": {"OCP-2": {
            "untestable_dependencies": {"disabled": True}
        }}}

        disabled = _CONTEXT.helper.score_in_temp_project(
            rule_path,
            config,
            {"untestable_dependencies": 1},
            "OCP-2",
        )
        sibling = _CONTEXT.helper.score_in_temp_project(
            rule_path,
            config,
            {"testable_direct_count": 1},
            "OCP-2",
        )

        self.assertEqual(disabled["final_severity"], "COMPLIANT")
        self.assertEqual(sibling["final_severity"], "MINOR")
