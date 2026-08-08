"""
solid-description: Validates that metric definitions remain synchronized across all specification sources.
solid-category: unit-test
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "mcp-server"))

from metric_discoverer import MetricDiscoverer

REFS_ROOT = Path(__file__).resolve().parents[2] / "references"

COVERED_METRICS = frozenset([
    ("CS", "CS-1", "static_logic_count"),
    ("CS", "CS-2", "class_struct_count"),
    ("CS", "CS-3", "inline_type_count"),
    ("DRY", "DRY-1", "reuse_misses"),
    ("DRY", "DRY-2", "duplicate_sites"),
    ("DRY", "DRY-3", "missing_abstractions"),
    ("FM", "FM-1", "missing_frontmatter_count"),
    ("FM", "FM-2", "name_mismatch_count"),
    ("FM", "FM-3", "invalid_category_count"),
    ("FM", "FM-4", "incorrect_stack_count"),
    ("FM", "FM-5", "bad_description_count"),
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

_DISCOVERER = MetricDiscoverer(REFS_ROOT)
_ALL = _DISCOVERER.discover()


class TestMetricCoverage(unittest.TestCase):
    """Validates that frontmatter bands and COVERED_METRICS stay in sync with rule.md."""

    def test_frontmatter_bands_covers_all_rule_metrics(self):
        """Every metric_id in <definition> or <detection> blocks must exist in bands: frontmatter."""
        gaps = []
        for rule_path in _DISCOVERER.all_rule_paths():
            xml_ids = _DISCOVERER.xml_metric_ids(rule_path)
            fm_ids = _DISCOVERER.frontmatter_metric_ids(rule_path)
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
        discovered = set(_ALL.keys())
        missing = discovered - COVERED_METRICS
        stale = COVERED_METRICS - discovered
        msgs = []
        if missing:
            msgs.append(
                "Metrics in rule.md NOT in COVERED_METRICS — add to COVERED_METRICS:\n"
                + "\n".join(f"  {m}" for m in sorted(missing))
            )
        if stale:
            msgs.append(
                "Stale entries in COVERED_METRICS not found in rule.md — remove:\n"
                + "\n".join(f"  {m}" for m in sorted(stale))
            )
        if msgs:
            self.fail("\n\n".join(msgs))


if __name__ == "__main__":
    unittest.main()
