"""Validates snapshot selection and normalized metadata before semantic lookup."""

from unittest import TestCase

from gate.dict_extension_lookup import DictExtensionLookup
from harness.flow_validation_error import FlowValidationError
from review.prepare_review_input import PrepareReviewInput
from review.prepare_review_operation_factory import PrepareReviewOperationFactory
from source.analysis.provenance.resolve_type_inspections_input import (
    ResolveTypeInspectionsInput,
)
from source.analysis.provenance.type_inspection_preparation_parser import (
    TypeInspectionPreparationParser,
)
from source.resolved_source_analyzer_factory import ResolvedSourceAnalyzerFactory
from source.source_language_detector import SourceLanguageDetector
from source.source_search_context import SourceSearchContext
from source.text_analysis_source import TextAnalysisSource


class TestTypeInspectionPreparation(TestCase):
    def setUp(self):
        self.source = "struct Consumer { func use(_ value: Any) { _ = value as? One } }\nstruct Other { func use(_ other: Any) { _ = other is Two } }"
        self.normalizer = PrepareReviewOperationFactory().make()
        self.prepared = self.normalizer.execute(
            PrepareReviewInput(
                target=TextAnalysisSource(
                    text=self.source,
                    virtual_path="/project/WithoutSuffix",
                    file_extension=".swift",
                )
            )
        )
        self.parser = TypeInspectionPreparationParser(
            analyzer=ResolvedSourceAnalyzerFactory().make(),
            languages=SourceLanguageDetector(DictExtensionLookup({".swift": "swift"})),
        )

    def test_unit_scope_uses_the_normalized_extension_not_the_path_suffix(self):
        unit = self.prepared.units[0]
        result = self.parser.parse(
            ResolveTypeInspectionsInput(
                target=unit.target,
                context=self.prepared.source_context,
                file_extension=unit.applicability.file_extension,
            )
        )
        self.assertEqual(result.language, "swift")
        self.assertEqual(
            [fact.expression for fact in result.inspections], ["value as? One"]
        )
        self.assertEqual(result.limitations, [])

    def test_file_scope_preserves_all_inspections_in_source_order(self):
        result = self.parser.parse(
            ResolveTypeInspectionsInput(
                target=self.prepared.review_file.target,
                context=self.prepared.source_context,
                file_extension=".swift",
            )
        )
        self.assertEqual(
            [fact.expression for fact in result.inspections],
            ["value as? One", "other is Two"],
        )

    def test_missing_and_duplicate_snapshots_are_rejected(self):
        snapshot = self.prepared.source_context.sources[0]
        for sources in [[], [snapshot, snapshot]]:
            with (
                self.subTest(count=len(sources)),
                self.assertRaisesRegex(FlowValidationError, "snapshot"),
            ):
                self.parser.parse(
                    ResolveTypeInspectionsInput(
                        target=self.prepared.units[0].target,
                        context=SourceSearchContext(sources=sources),
                        file_extension=".swift",
                    )
                )

    def test_incomplete_syntax_is_not_a_complete_inventory(self):
        prepared = self.normalizer.execute(
            PrepareReviewInput(
                target=TextAnalysisSource(
                    text=self.source + "\nfunc incomplete(",
                    virtual_path="/project/Partial.swift",
                )
            )
        )
        result = self.parser.parse(
            ResolveTypeInspectionsInput(
                target=prepared.review_file.target,
                context=prepared.source_context,
                file_extension=".swift",
            )
        )
        self.assertTrue(result.limitations)
