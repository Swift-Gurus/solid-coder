"""
solid-name: test_rule_applicability_context_resolver
solid-category: unit-test
solid-spec: [SPEC-039, SPEC-040]
solid-description: Verifies source analysis becomes one deterministic rule-applicability context per unit.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from findings.review_unit_kind import ReviewUnitKind
from harness.ordered_string_collector import OrderedStringCollector
from harness.rule_applicability_context_resolver import RuleApplicabilityContextResolver
from source.source_analysis import SourceAnalysis
from source.source_analysis_decision import SourceAnalysisDecision
from source.source_evidence import SourceEvidence
from source.source_line_range import SourceLineRange
from source.source_unit import SourceUnit
from source.technology_detection import TechnologyDetection
from source.technology_detection_scope import TechnologyDetectionScope


class TestRuleApplicabilityContextResolver(unittest.TestCase):

    def test_inherits_file_tags_and_selects_only_the_target_units_tags(self):
        dashboard = self._unit("struct:DashboardView:2", "DashboardView", 2)
        store = self._unit("class:Store:5", "Store", 5, ReviewUnitKind.CLASS)
        analysis = SourceAnalysis(
            source_identity="Feature.swift",
            file_extension=".swift",
            decision=SourceAnalysisDecision.PARSED,
            units=[dashboard, store],
            detections=[
                self._detection("ui", TechnologyDetectionScope.FILE, "Feature.swift"),
                self._detection("swiftui", TechnologyDetectionScope.FILE, "Feature.swift"),
                self._detection("ui", TechnologyDetectionScope.FILE, "Feature.swift"),
                self._detection("view", TechnologyDetectionScope.UNIT, dashboard.identity),
                self._detection("test-double", TechnologyDetectionScope.UNIT, store.identity),
            ],
        )

        context = RuleApplicabilityContextResolver(
            OrderedStringCollector()
        ).resolve(analysis, dashboard)

        self.assertEqual(context.file_extension, ".swift")
        self.assertEqual(context.unit_kind, ReviewUnitKind.STRUCT)
        self.assertEqual(context.tags, ["ui", "swiftui", "view"])

    def _unit(
        self,
        identity: str,
        name: str,
        line: int,
        kind: ReviewUnitKind = ReviewUnitKind.STRUCT,
    ) -> SourceUnit:
        return SourceUnit(
            identity=identity,
            kind=kind,
            name=name,
            span=SourceLineRange(start=line, end=line),
            start_offset=0,
            end_offset=1,
        )

    def _detection(
        self,
        tag: str,
        scope: TechnologyDetectionScope,
        scope_identity: str,
    ) -> TechnologyDetection:
        return TechnologyDetection(
            tag=tag,
            detector_identity="test-detector",
            scope=scope,
            scope_identity=scope_identity,
            evidence=[
                SourceEvidence(
                    fact=tag,
                    span=SourceLineRange(start=1, end=1),
                )
            ],
        )


if __name__ == "__main__":
    unittest.main()
