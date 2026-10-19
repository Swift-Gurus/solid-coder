"""Checks composed Swift inspection evidence on exact unwritten buffers."""

from pathlib import Path
from shutil import which
from tempfile import TemporaryDirectory
from unittest import TestCase, skipUnless

from gate.default_exclusion_checker_factory import DefaultExclusionCheckerFactory
from review.prepare_review_input import PrepareReviewInput
from review.prepare_review_operation_factory import PrepareReviewOperationFactory
from source.analysis.provenance.sourcekit_document_factory import SourceKitDocumentFactory
from source.analysis.provenance.swift_inspection_session_factory import SwiftInspectionSessionFactory
from source.resolved_analysis_source import ResolvedAnalysisSource
from source.resolved_source_analyzer_factory import ResolvedSourceAnalyzerFactory
from source.text_analysis_source import TextAnalysisSource


@skipUnless(which("xcrun") or which("sourcekit-lsp"), "Requires installed Swift semantic tooling")
class TestSwiftInspectionSession(TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(prefix="inspection-session-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / ".git").mkdir()
        self.path = self.root / "Unwritten.swift"
        self.factory = SwiftInspectionSessionFactory(SourceKitDocumentFactory(), DefaultExclusionCheckerFactory())

    def resolve(self, source):
        prepared = PrepareReviewOperationFactory().make().execute(PrepareReviewInput(
            target=TextAnalysisSource(text=source, virtual_path=str(self.path)),
        ))
        analysis = ResolvedSourceAnalyzerFactory().make().analyze(ResolvedAnalysisSource(
            identity=str(self.path), file_extension=".swift", text=source,
        ))
        with self.factory.open(prepared.source_context.sources[0], self.root) as parser:
            facts = [parser.parse(inspection) for inspection in analysis.type_inspections]
        self.assertFalse(self.path.exists())
        return facts

    def test_owned_contract_and_destination_remain_distinct(self):
        facts = self.resolve("protocol Service {}\nstruct Concrete: Service {}\nfunc use(_ value: any Service) { _ = value as? Concrete }")
        self.assertTrue(facts[0].verified, facts[0].limitations)
        self.assertEqual(facts[0].contract.ownership, "developer")
        self.assertEqual(facts[0].destination.ownership, "developer")
        self.assertNotEqual(facts[0].contract.resolution.symbol_id, facts[0].value.resolution.symbol_id)

    def test_runtime_type_query_requires_no_destination(self):
        facts = self.resolve("protocol Service {}\nfunc use(_ value: any Service) { _ = type(of: value) }")
        self.assertTrue(facts[0].verified, facts[0].limitations)
        self.assertEqual(facts[0].destination.ownership, "unknown")
        self.assertEqual(facts[0].limitations, [])

    def test_unresolved_binding_does_not_erase_an_independent_verified_inspection(self):
        facts = self.resolve("protocol Service {}\nstruct Concrete: Service {}\nfunc use(_ value: any Service) { _ = value as? Concrete; let inferred = provider(); _ = inferred as? Concrete }")
        self.assertEqual([fact.verified for fact in facts], [True, False])
        self.assertTrue(facts[1].limitations)
