"""Verifies disabled principle configuration overrides."""

import unittest
from pathlib import Path

from config_override_test_context import ConfigOverrideTestContext


_CONTEXT = ConfigOverrideTestContext(Path(__file__).resolve().parents[3] / "references")


"""
solid-name: DisabledPrincipleOverrideTests
solid-category: unit-test
solid-description: Verifies disabled principle overrides make every configured metric compliant.
"""
class DisabledPrincipleOverrideTests(unittest.TestCase):
    def test_disabled_principle_forces_all_metrics_compliant(self):
        seen: set[str] = set()
        for (config_key, metric_id, variable), (bands, rule_path) in _CONTEXT.metrics.items():
            if config_key in seen:
                continue
            seen.add(config_key)
            severe_value = _CONTEXT.extractor.severe_value(bands)
            if severe_value is None:
                continue
            result = _CONTEXT.helper.score_in_temp_project(
                rule_path,
                config={config_key: {"disabled": True}},
                unit_metrics={variable: severe_value},
                metric_id=metric_id,
            )
            self.assertEqual(result["final_severity"], "COMPLIANT")
