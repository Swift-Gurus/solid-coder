"""
solid-description: Validates configurable severity bands — disabled metrics, threshold overrides, nested .solid-coder.yml merging — for every metric discovered from rule.md frontmatter.
solid-category: unit-test
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scoring.severity_scorer import SeverityScorer
from tests.metric_discoverer import MetricDiscoverer
from tests.band_value_extractor import BandValueExtractor
from tests.config_test_writer import ConfigTestWriter

REFS_ROOT = Path(__file__).resolve().parents[2] / "references"

# ── Coverage registry ──────────────────────────────────────────────────────────
# Every (CONFIG_KEY, METRIC_ID, VARIABLE) triple found in frontmatter must appear
# here. CONFIG_KEY = metric_id.split('-')[0].upper() — the key used in .solid-coder.yml.
# Adding a metric to rule.md frontmatter without adding to COVERED_METRICS causes
# test_coverage_is_complete to fail with an explicit message naming the gap.
COVERED_METRICS = frozenset([
    ("CS", "CS-1", "static_logic_count"),
    ("CS", "CS-2", "class_struct_count"),
    ("CS", "CS-3", "inline_type_count"),
    ("DRY", "DRY-1", "reuse_misses"),
    ("DRY", "DRY-2", "duplicate_sites"),
    ("DRY", "DRY-3", "missing_abstractions"),
    ("ISP", "ISP-1", "width"),
    ("ISP", "ISP-2", "min_coverage"),
    ("ISP", "ISP-3", "cohesion_groups"),
    ("LSP", "LSP-1", "type_checks"),
    ("LSP", "LSP-2", "contract_violations"),
    ("LSP", "LSP-3", "empty_methods"),
    ("LSP", "LSP-3", "fatal_error_methods"),
    ("OCP", "OCP-1", "sealed_variation_points"),
    ("OCP", "OCP-2", "testable_direct_count"),
    ("OCP", "OCP-2", "untestable_dependencies"),
    ("SC", "SC-1", "model_mixing"),
    ("SC", "SC-2", "orphaned_tasks"),
    ("SC", "SC-3", "safety_bypasses"),
    ("SC", "SC-4", "independent_sequential_awaits"),
    ("SC", "SC-5", "blocking_bridges"),
    ("SC", "SC-6", "raw_duration_count"),
    ("SRP", "SRP-1", "verb_count"),
    ("SRP", "SRP-2", "cohesion_groups"),
    ("SRP", "SRP-3", "stakeholder_count"),
    ("SUI", "SUI-1", "body_nesting_depth"),
    ("SUI", "SUI-1", "view_expression_count"),
    ("SUI", "SUI-2", "impure_count"),
    ("SUI", "SUI-3", "max_modifier_chain"),
    ("SUI", "SUI-4", "vm_injection_style"),
    ("SUI", "SUI-5", "preview_only_count"),
    ("SUI", "SUI-6", "views_without_preview_count"),
    ("SUI", "SUI-7", "bad_accessibility_count"),
    ("SUI", "SUI-8", "fixed_frame_count"),
    ("SUI", "SUI-9", "over_isolated_count"),
    ("TEST", "TEST-1", "isolation_violations"),
    ("TEST", "TEST-2", "structure_violations"),
    ("TEST", "TEST-3", "naming_violations"),
    ("TEST", "TEST-4", "test_double_violations"),
    ("TEST", "TEST-5", "setup_violations"),
    ("TEST", "TEST-6", "framework_violations"),
    ("UITEST", "UITEST-1", "flow_violations"),
    ("UITEST", "UITEST-2", "base_class_violations"),
    ("UITEST", "UITEST-3", "grouping_violations"),
    ("UITEST", "UITEST-4", "sync_violations"),
    ("UITEST", "UITEST-5", "identifier_violations"),
])


class TestConfigBands(unittest.TestCase):
    """Orchestrates config-bands tests using injected helpers.

    All discovery, value derivation, and config writing is delegated to
    MetricDiscoverer, BandValueExtractor, and ConfigTestWriter.
    """

    def setUp(self):
        self._discoverer = MetricDiscoverer(REFS_ROOT)
        self._extractor = BandValueExtractor()
        self._writer = ConfigTestWriter()
        self._all = self._discoverer.discover()

    def _scorer(self, rule_path: Path, project_root: str = "") -> SeverityScorer:
        return SeverityScorer.from_folder(rule_path.parent, project_root=project_root or None)

    # ── Coverage ───────────────────────────────────────────────────────────────

    def test_frontmatter_bands_covers_all_rule_metrics(self):
        """Every metric_id in <definition> or <detection> blocks must exist in bands: frontmatter.

        Fails with an explicit message if a metric is documented in rule.md but
        missing from the frontmatter bands — meaning it would be silently unscored.
        """
        gaps = []
        for rule_path in self._discoverer.all_rule_paths():
            xml_ids = self._discoverer.xml_metric_ids(rule_path)
            fm_ids = self._discoverer.frontmatter_metric_ids(rule_path)
            missing = xml_ids - fm_ids
            if missing:
                gaps.append(f"{rule_path.relative_to(REFS_ROOT.parent)}: "
                            f"metrics in definition/detection but not in bands frontmatter: "
                            f"{sorted(missing)}")
        if gaps:
            self.fail(
                "Add missing metrics to the 'bands:' frontmatter section in each rule.md:\n\n"
                + "\n".join(gaps)
            )

    def test_coverage_is_complete(self):
        """Fails explicitly if frontmatter adds a metric not in COVERED_METRICS."""
        discovered = set(self._all.keys())
        missing = discovered - COVERED_METRICS
        stale = COVERED_METRICS - discovered
        msgs = []
        if missing:
            msgs.append(
                "Metrics in rule.md NOT in COVERED_METRICS — add to TestConfigBands.COVERED_METRICS:\n"
                + "\n".join(f"  {m}" for m in sorted(missing))
            )
        if stale:
            msgs.append(
                "Stale entries in COVERED_METRICS not found in rule.md — remove:\n"
                + "\n".join(f"  {m}" for m in sorted(stale))
            )
        if msgs:
            self.fail("\n\n".join(msgs))

    # ── disabled: true at metric level ─────────────────────────────────────────

    def test_disabled_metric_always_returns_compliant(self):
        """Every metric: disabled:true in config → COMPLIANT regardless of value."""
        for (cfg_key, metric_id, variable), (bands, rule_path) in self._all.items():
            with self.subTest(cfg_key=cfg_key, metric_id=metric_id, variable=variable):
                severe_val = self._extractor.severe_value(bands)
                if severe_val is None:
                    continue
                with tempfile.TemporaryDirectory() as tmp:
                    src = Path(tmp) / "src" / "Foo.swift"
                    src.parent.mkdir()
                    self._writer.write(Path(tmp), {cfg_key: {metric_id: {variable: {"disabled": True}}}})
                    result = self._scorer(rule_path, tmp).score_unit(
                        {variable: severe_val}, metric_id, str(src)
                    )
                    self.assertEqual(result["final_severity"], "COMPLIANT",
                                     f"{cfg_key}/{metric_id}/{variable}={severe_val}: disabled → COMPLIANT")

    # ── disabled: true at principle level ──────────────────────────────────────

    def test_disabled_principle_forces_all_metrics_compliant(self):
        """Disabling a full principle skips all its metrics."""
        seen = set()
        for (cfg_key, metric_id, variable), (bands, rule_path) in self._all.items():
            if cfg_key in seen:
                continue
            seen.add(cfg_key)
            severe_val = self._extractor.severe_value(bands)
            if severe_val is None:
                continue
            with self.subTest(cfg_key=cfg_key, metric_id=metric_id):
                with tempfile.TemporaryDirectory() as tmp:
                    src = Path(tmp) / "src" / "Foo.swift"
                    src.parent.mkdir()
                    self._writer.write(Path(tmp), {cfg_key: {"disabled": True}})
                    result = self._scorer(rule_path, tmp).score_unit(
                        {variable: severe_val}, metric_id, str(src)
                    )
                    self.assertEqual(result["final_severity"], "COMPLIANT",
                                     f"{cfg_key} disabled: {metric_id}/{variable}={severe_val} → COMPLIANT")

    # ── Threshold override ─────────────────────────────────────────────────────

    def test_threshold_override_changes_severity(self):
        """Raising the severe threshold makes the original severe value no longer SEVERE."""
        for (cfg_key, metric_id, variable), (bands, rule_path) in self._all.items():
            op, threshold = self._extractor.numeric_severe_op(bands)
            if op is None:
                continue
            original_val = self._extractor.severe_value(bands)
            raised = threshold + 5

            with self.subTest(cfg_key=cfg_key, metric_id=metric_id, variable=variable):
                with tempfile.TemporaryDirectory() as tmp:
                    src = Path(tmp) / "src" / "Foo.swift"
                    src.parent.mkdir()
                    self._writer.write(Path(tmp), {
                        cfg_key: {metric_id: {variable: {"severe": {op: raised}}}}
                    })
                    result = self._scorer(rule_path, tmp).score_unit(
                        {variable: original_val}, metric_id, str(src)
                    )
                    self.assertNotEqual(
                        result["final_severity"], "SEVERE",
                        f"{cfg_key}/{metric_id}/{variable}={original_val} with {op}={raised} "
                        f"(was {threshold}) should not be SEVERE"
                    )

    # ── Nested config ──────────────────────────────────────────────────────────

    def test_nested_config_applies_only_to_files_in_subdirectory(self):
        """Child .solid-coder.yml disables a metric only for files within its directory."""
        bands, rule_path = self._all[("SRP", "SRP-1", "verb_count")]
        severe_val = self._extractor.severe_value(bands)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subdir = root / "src" / "tests"
            subdir.mkdir(parents=True)
            self._writer.write(root, {})
            self._writer.write(subdir, {"SRP": {"SRP-1": {"verb_count": {"disabled": True}}}})

            scorer = self._scorer(rule_path, tmp)

            r_in = scorer.score_unit({"verb_count": severe_val}, "SRP-1", str(subdir / "FooTests.swift"))
            self.assertEqual(r_in["final_severity"], "COMPLIANT",
                             "Inside subdir: child config disables verb_count → COMPLIANT")

            r_out = scorer.score_unit({"verb_count": severe_val}, "SRP-1", str(root / "src" / "Foo.swift"))
            self.assertEqual(r_out["final_severity"], "SEVERE",
                             "Outside subdir: child config does not apply → SEVERE")

    # ── Partial merge ──────────────────────────────────────────────────────────

    def test_partial_merge_preserves_sibling_variable(self):
        """Overriding one variable does not affect sibling variables in the same metric."""
        _, rule_path = self._all[("OCP", "OCP-2", "untestable_dependencies")]

        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src" / "Foo.swift"
            src.parent.mkdir()
            self._writer.write(Path(tmp), {
                "OCP": {"OCP-2": {"untestable_dependencies": {"disabled": True}}}
            })
            scorer = self._scorer(rule_path, tmp)

            r1 = scorer.score_unit({"untestable_dependencies": 1}, "OCP-2", str(src))
            self.assertEqual(r1["final_severity"], "COMPLIANT", "Disabled variable → COMPLIANT")

            r2 = scorer.score_unit({"testable_direct_count": 1}, "OCP-2", str(src))
            self.assertEqual(r2["final_severity"], "MINOR", "Sibling unaffected → MINOR")


if __name__ == "__main__":
    unittest.main()
