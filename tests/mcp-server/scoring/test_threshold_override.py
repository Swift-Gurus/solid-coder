"""Verifies configurable severity threshold overrides."""

import unittest
from pathlib import Path

from config_override_test_context import ConfigOverrideTestContext


_CONTEXT = ConfigOverrideTestContext(Path(__file__).resolve().parents[3] / "references")


"""
solid-name: ThresholdOverrideTests
solid-category: unit-test
solid-description: Verifies raised severity thresholds change matching outcomes.
"""
class ThresholdOverrideTests(unittest.TestCase):
    def test_threshold_override_changes_severity(self):
        for (config_key, metric_id, variable), (bands, rule_path) in _CONTEXT.metrics.items():
            operator, threshold = _CONTEXT.extractor.numeric_severe_op(bands)
            if operator is None:
                continue
            result = _CONTEXT.helper.score_in_temp_project(
                rule_path,
                config={config_key: {metric_id: {variable: {
                    "severe": {operator: threshold + 5}
                }}}},
                unit_metrics={variable: _CONTEXT.extractor.severe_value(bands)},
                metric_id=metric_id,
            )
            self.assertNotEqual(result["final_severity"], "SEVERE")
