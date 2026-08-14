"""Verifies disabled metric configuration overrides."""

import unittest
from pathlib import Path

from config_override_test_context import ConfigOverrideTestContext


_CONTEXT = ConfigOverrideTestContext(Path(__file__).resolve().parents[3] / "references")


"""
solid-name: DisabledMetricOverrideTests
solid-category: unit-test
solid-description: Verifies disabled metric overrides always produce compliant scoring.
"""
class DisabledMetricOverrideTests(unittest.TestCase):
    def test_disabled_metric_always_returns_compliant(self):
        for (config_key, metric_id, variable), (bands, rule_path) in _CONTEXT.metrics.items():
            with self.subTest(config_key=config_key, metric_id=metric_id, variable=variable):
                severe_value = _CONTEXT.extractor.severe_value(bands)
                if severe_value is None:
                    continue
                result = _CONTEXT.helper.score_in_temp_project(
                    rule_path,
                    config={config_key: {metric_id: {variable: {"disabled": True}}}},
                    unit_metrics={variable: severe_value},
                    metric_id=metric_id,
                )
                self.assertEqual(result["final_severity"], "COMPLIANT")
