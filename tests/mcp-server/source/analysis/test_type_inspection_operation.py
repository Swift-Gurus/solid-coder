"""Validates semantic operation dispatch, coverage and bounded failures."""

from contextlib import nullcontext
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock

from gate.dict_extension_lookup import DictExtensionLookup
from harness.project_context import ProjectDirectory
from harness.template_value_rendering import TemplateValueRendering
from review.prepare_review_input import PrepareReviewInput
from review.prepare_review_operation_factory import PrepareReviewOperationFactory
from source.analysis.provenance.prepared_type_inspections import PreparedTypeInspections
from source.analysis.provenance.resolve_type_inspections_input import ResolveTypeInspectionsInput
from source.analysis.provenance.source_declaration_symbol import SourceDeclarationSymbol
from source.analysis.provenance.source_symbol_provenance import SourceSymbolProvenance
from source.analysis.provenance.source_type_inspection_operation import SourceTypeInspectionOperation
from source.analysis.provenance.source_type_inspection_provenance import SourceTypeInspectionProvenance
from source.analysis.provenance.sourcekit_document_factory import SemanticDocumentOpening
from source.analysis.provenance.type_inspection_preparation_parser import TypeInspectionPreparationParser
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.language_source_analyzer_resolving import LanguageSourceAnalyzerResolving
from source.resolved_source_analyzer_factory import ResolvedSourceAnalyzerFactory
from source.source_language_detector import SourceLanguageDetector
from source.text_analysis_source import TextAnalysisSource
from source.source_search_context import SourceSearchContext


class TestTypeInspectionOperation(TestCase):
    def setUp(self):
        normalized = PrepareReviewOperationFactory().make().execute(PrepareReviewInput(target=TextAnalysisSource(
            text="struct Consumer { func use(_ value: Any) { _ = value as? A; _ = value as? B } }",
            virtual_path="/project/Source.swift",
        )))
        self.input = ResolveTypeInspectionsInput(target=normalized.units[0].target, context=normalized.source_context, file_extension=".swift")
        self.prepared = TypeInspectionPreparationParser(
            ResolvedSourceAnalyzerFactory().make(), SourceLanguageDetector(DictExtensionLookup({".swift": "swift"})),
        ).parse(self.input)
        self.preparation = Mock(spec=SourceSyntaxParsing)
        self.preparation.parse.return_value = self.prepared
        self.parser = Mock(spec=SourceSyntaxParsing)
        self.parser.parse.side_effect = [self.fact(inspection) for inspection in self.prepared.inspections]
        self.sessions = Mock(spec=SemanticDocumentOpening)
        self.sessions.open.return_value = nullcontext(self.parser)
        self.resolver = Mock(spec=LanguageSourceAnalyzerResolving)
        self.resolver.resolve.return_value = self.sessions
        self.renderer = Mock(spec=TemplateValueRendering)
        self.renderer.render.return_value = "Compact inspection facts."
        self.operation = SourceTypeInspectionOperation(self.preparation, self.resolver, ProjectDirectory(path=Path("/project")), self.renderer)

    def fact(self, inspection):
        provenance = SourceSymbolProvenance(
            resolution=SourceDeclarationSymbol(symbol_id="fixture", declaration_path=Path("/project/Source.swift")),
            project_root=Path("/project"), ownership="developer", declaration_path=Path("/project/Source.swift"), reason="Verified fixture.",
        )
        return SourceTypeInspectionProvenance(inspection=inspection, value=provenance, contract=provenance, destination=provenance, verified=True)

    def test_one_session_covers_ordered_inspections(self):
        result = self.operation.execute(self.input)
        self.assertEqual([fact.inspection for fact in result.inspections], self.prepared.inspections)
        self.assertTrue(all(fact.verified for fact in result.inspections))
        self.sessions.open.assert_called_once_with(self.prepared.snapshot, Path("/project"))
        self.resolver.resolve.assert_called_once_with("swift")
        self.assertEqual(result.context, "Compact inspection facts.")
        self.renderer.render.assert_called_once_with(result.inspections)

    def test_empty_complete_inventory_does_not_open_a_semantic_session(self):
        self.preparation.parse.return_value = PreparedTypeInspections(snapshot=self.prepared.snapshot, language="swift")
        self.assertEqual(self.operation.execute(self.input).inspections, [])
        self.resolver.resolve.assert_not_called()
        self.sessions.open.assert_not_called()

    def test_partial_empty_inventory_preserves_its_limitation(self):
        self.preparation.parse.return_value = PreparedTypeInspections(snapshot=self.prepared.snapshot, language="swift", limitations=["Incomplete syntax."])
        self.assertEqual(self.operation.execute(self.input).limitations, ["Incomplete syntax."])
        self.sessions.open.assert_not_called()

    def test_missing_language_capability_is_unavailable_not_compliant(self):
        self.resolver.resolve.return_value = None
        result = self.operation.execute(self.input)
        self.assertEqual(len(result.inspections), 2)
        self.assertTrue(all(not fact.verified for fact in result.inspections))
        self.assertTrue(result.limitations)

    def test_missing_tooling_retains_every_inspection(self):
        self.sessions.open.side_effect = FileNotFoundError("semantic tool missing")
        result = self.operation.execute(self.input)
        self.assertEqual(len(result.inspections), 2)
        self.assertIn("semantic tool missing", result.inspections[0].contract.reason)

    def test_timeout_preserves_prior_verified_evidence(self):
        self.parser.parse.side_effect = [self.fact(self.prepared.inspections[0]), TimeoutError("lookup deadline")]
        result = self.operation.execute(self.input)
        self.assertEqual([fact.verified for fact in result.inspections], [True, False])
        self.assertEqual([fact.inspection for fact in result.inspections], self.prepared.inspections)
        self.assertIn("lookup deadline", result.inspections[1].contract.reason)

    def test_provider_cannot_change_prepared_inspection_identity(self):
        self.parser.parse.side_effect = [self.fact(self.prepared.inspections[1])]
        result = self.operation.execute(self.input)
        self.assertTrue(all(not fact.verified for fact in result.inspections))
        self.assertEqual([fact.inspection for fact in result.inspections], self.prepared.inspections)

    def test_unopened_prospective_sibling_cannot_supply_verified_contract_evidence(self):
        sibling = self.prepared.snapshot.model_copy(update={"path": Path("/project/Other.swift"), "source_identity": "/project/Other.swift"})
        contract = SourceSymbolProvenance(
            resolution=SourceDeclarationSymbol(symbol_id="other-contract", declaration_path=sibling.path),
            project_root=Path("/project"), ownership="developer", declaration_path=sibling.path,
            reason="The service resolved a declaration in another file.",
        )
        first = self.fact(self.prepared.inspections[0]).model_copy(update={"contract": contract})
        self.parser.parse.side_effect = [first, self.fact(self.prepared.inspections[1])]
        operation_input = self.input.model_copy(update={"context": SourceSearchContext(sources=[self.prepared.snapshot, sibling])})
        result = self.operation.execute(operation_input)
        self.assertEqual([fact.verified for fact in result.inspections], [False, True])
        self.assertIn("prospective", result.inspections[0].limitations[0])
