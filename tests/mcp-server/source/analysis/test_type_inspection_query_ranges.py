"""Preserves exact query-role ranges before any semantic service is called."""

from unittest import TestCase

from source.resolved_analysis_source import ResolvedAnalysisSource
from source.resolved_source_analyzer_factory import ResolvedSourceAnalyzerFactory


class TestTypeInspectionQueryRanges(TestCase):
    def analyze(self, source):
        return ResolvedSourceAnalyzerFactory().make().analyze(ResolvedAnalysisSource(
            identity="/project/Prospective.swift", file_extension=".swift", text=source,
        ))

    def test_value_and_destination_ranges_are_distinct_and_exact(self):
        for expression in ["value as? Module.Concrete", "value as! Module.Concrete", "value is Module.Concrete"]:
            with self.subTest(expression=expression):
                source = f"func use(_ value: Any) {{ _ = {expression} }}"
                fact = self.analyze(source).type_inspections[0]
                self.assertIsNotNone(fact.operand_range)
                self.assertIsNotNone(fact.destination_range)
                self.assertEqual(source.encode()[fact.operand_range.start:fact.operand_range.end].decode(), "value")
                self.assertEqual(source.encode()[fact.destination_range.start:fact.destination_range.end].decode(), "Module.Concrete")

    def test_type_query_has_no_destination(self):
        source = "func use(_ café: Any) { _ = type(of: café) }"
        fact = self.analyze(source).type_inspections[0]
        self.assertIsNotNone(fact.operand_range)
        self.assertEqual(source.encode()[fact.operand_range.start:fact.operand_range.end].decode(), "café")
        self.assertIsNone(fact.destination_range)

    def test_pattern_never_fabricates_a_value_range(self):
        source = "func use(_ value: Any) { switch value { case is Concrete: break; default: break } }"
        fact = self.analyze(source).type_inspections[0]
        self.assertIsNone(fact.operand_range)
        self.assertIsNotNone(fact.destination_range)
        self.assertEqual(source.encode()[fact.destination_range.start:fact.destination_range.end].decode(), "Concrete")
