"""
solid-description: Validates that configuration overrides are correctly applied.
solid-category: unit-test
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "mcp-server"))

from scoring.severity_scorer import SeverityScorer
from metric_discoverer import MetricDiscoverer
from band_value_extractor import BandValueExtractor
from config_test_writer import ConfigTestWriter
from config_bands_test_helper import ConfigBandsTestHelper

REFS_ROOT = Path(__file__).resolve().parents[2] / "references"

_ALL = MetricDiscoverer(REFS_ROOT).discover()
_EXTRACTOR = BandValueExtractor()
_HELPER = ConfigBandsTestHelper(writer=ConfigTestWriter(), scorer_factory=SeverityScorer.from_folder)


class TestConfigOverrides(unittest.TestCase):
    """Validates that .solid-coder/severity-bands.yml overrides apply correctly."""

    def test_disabled_metric_always_returns_compliant(self):
        """Every metric: disabled:true in config → COMPLIANT regardless of value."""
        for (cfg_key, metric_id, variable), (bands, rule_path) in _ALL.items():
            with self.subTest(cfg_key=cfg_key, metric_id=metric_id, variable=variable):
                severe_val = _EXTRACTOR.severe_value(bands)
                if severe_val is None:
                    continue
                result = _HELPER.score_in_temp_project(
                    rule_path,
                    config={cfg_key: {metric_id: {variable: {"disabled": True}}}},
                    unit_metrics={variable: severe_val},
                    metric_id=metric_id,
                )
                self.assertEqual(result["final_severity"], "COMPLIANT",
                                 f"{cfg_key}/{metric_id}/{variable}={severe_val}: disabled → COMPLIANT")

    def test_disabled_principle_forces_all_metrics_compliant(self):
        """Disabling a full principle skips all its metrics."""
        seen = set()
        for (cfg_key, metric_id, variable), (bands, rule_path) in _ALL.items():
            if cfg_key in seen:
                continue
            seen.add(cfg_key)
            severe_val = _EXTRACTOR.severe_value(bands)
            if severe_val is None:
                continue
            with self.subTest(cfg_key=cfg_key, metric_id=metric_id):
                result = _HELPER.score_in_temp_project(
                    rule_path,
                    config={cfg_key: {"disabled": True}},
                    unit_metrics={variable: severe_val},
                    metric_id=metric_id,
                )
                self.assertEqual(result["final_severity"], "COMPLIANT",
                                 f"{cfg_key} disabled: {metric_id}/{variable}={severe_val} → COMPLIANT")

    def test_threshold_override_changes_severity(self):
        """Raising the severe threshold makes the original severe value no longer SEVERE."""
        for (cfg_key, metric_id, variable), (bands, rule_path) in _ALL.items():
            op, threshold = _EXTRACTOR.numeric_severe_op(bands)
            if op is None:
                continue
            original_val = _EXTRACTOR.severe_value(bands)
            raised = threshold + 5
            with self.subTest(cfg_key=cfg_key, metric_id=metric_id, variable=variable):
                result = _HELPER.score_in_temp_project(
                    rule_path,
                    config={cfg_key: {metric_id: {variable: {"severe": {op: raised}}}}},
                    unit_metrics={variable: original_val},
                    metric_id=metric_id,
                )
                self.assertNotEqual(
                    result["final_severity"], "SEVERE",
                    f"{cfg_key}/{metric_id}/{variable}={original_val} with {op}={raised} "
                    f"(was {threshold}) should not be SEVERE"
                )

    def test_partial_merge_preserves_sibling_variable(self):
        """Overriding one variable does not affect sibling variables in the same metric."""
        _, rule_path = _ALL[("OCP", "OCP-2", "untestable_dependencies")]
        config = {"OCP": {"OCP-2": {"untestable_dependencies": {"disabled": True}}}}

        r1 = _HELPER.score_in_temp_project(rule_path, config, {"untestable_dependencies": 1}, "OCP-2")
        self.assertEqual(r1["final_severity"], "COMPLIANT", "Disabled variable → COMPLIANT")

        r2 = _HELPER.score_in_temp_project(rule_path, config, {"testable_direct_count": 1}, "OCP-2")
        self.assertEqual(r2["final_severity"], "MINOR", "Sibling unaffected → MINOR")


if __name__ == "__main__":
    unittest.main()
