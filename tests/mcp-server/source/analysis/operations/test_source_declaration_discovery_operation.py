import tempfile
import unittest
from pathlib import Path

from harness.project_context import ProjectDirectory
from source.analysis.operations.discover_source_declaration_input import DiscoverSourceDeclarationInput
from source.analysis.operations.source_declaration_discovery_operation_factory import SourceDeclarationDiscoveryOperationFactory
from source.file_analysis_source import FileAnalysisSource
from source.prepare_search_targets_input import PrepareSearchTargetsInput
from source.prepare_search_targets_operation_factory import PrepareSearchTargetsOperationFactory
from source.search_target_granularity import SearchTargetGranularity
from source.source_search_context import SourceSearchContext


"""
solid-name: TestSourceDeclarationDiscoveryOperation
solid-category: integration-test
solid-spec: [SPEC-057]
solid-description: Verifies name-only bounded discovery finds related declarations and separate extensions while preserving source authority and uncertainty.
"""
class TestSourceDeclarationDiscoveryOperation(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.interface = self.root / "Reading.swift"
        self.interface.write_text("protocol Reading { func read() }\n")
        (self.root / "Store.swift").write_text("struct Store: Reading {}\n")
        (self.root / "Store+Helpers.swift").write_text("extension Store { func read() {} }\n")
        project = ProjectDirectory(path=self.root)
        self.sut = SourceDeclarationDiscoveryOperationFactory(project).make()
        prepared = PrepareSearchTargetsOperationFactory().make().execute(PrepareSearchTargetsInput(
            source=FileAnalysisSource(path=self.interface),
            granularity=SearchTargetGranularity.UNIT,
        ))
        self.target = prepared.targets[0]
        self.context = SourceSearchContext(sources=[prepared.snapshot])

    def discover(self, limit: int = 20):
        return self.sut.execute(DiscoverSourceDeclarationInput(
            target=self.target, context=self.context, max_candidates=limit,
        ))

    def test_name_query_finds_conformer_then_its_separate_extension(self) -> None:
        result = self.discover()

        self.assertEqual([query.terms for query in result.queries], [["Reading"], ["Store"]])
        self.assertEqual([related.declaration.name for related in result.related_declarations], ["Store"])
        self.assertNotIn(self.root / "Store+Helpers.swift", [candidate.path for candidate in result.searches[0].candidates])
        self.assertIn(str(self.root / "Store+Helpers.swift"), [item.source_identity for item in result.inventory.analyses])
        self.assertEqual(result.limitations, [])
        self.assertEqual(result.inventory.verification, "unverified_candidates")

    def test_each_source_is_analyzed_once_across_discovery_passes(self) -> None:
        result = self.discover()

        identities = [item.source_identity for item in result.inventory.analyses]
        self.assertEqual(len(identities), len(set(identities)))
        self.assertEqual(identities.count(str(self.interface)), 1)

    def test_prospective_interface_snapshot_wins_over_changed_disk(self) -> None:
        self.interface.write_text("struct Unrelated {}\n")

        result = self.discover()

        inspected = next(item for item in result.inventory.analyses if item.source_identity == str(self.interface))
        self.assertEqual(inspected.units[0].name, "Reading")
        self.assertEqual(result.declaration.unit_identity, self.target.unit_identity)

    def test_bound_is_reported_without_claiming_repository_completeness(self) -> None:
        result = self.discover(limit=1)

        self.assertTrue(any("limit" in reason for reason in result.limitations))
        self.assertEqual(result.inventory.verification, "unverified_candidates")

    def test_same_name_interfaces_retain_ambiguous_relationship(self) -> None:
        (self.root / "Other.swift").write_text("protocol Reading { func write() }\n")

        result = self.discover()

        self.assertEqual(result.related_declarations[0].relationship.status.value, "ambiguous")
        self.assertTrue(result.limitations)
