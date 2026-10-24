from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from git_working_tree_fixture import GitWorkingTreeFixture
from harness.project_context import ProjectDirectory
from source.analysis.operations.candidate_source_analysis_visitor import (
    CandidateSourceAnalysisVisitor,
)
from source.analysis.operations.source_candidate_analysis_operation import (
    SourceCandidateAnalysisOperation,
)
from source.file_analysis_source import FileAnalysisSource
from source.prepare_search_targets_input import PrepareSearchTargetsInput
from source.prepare_search_targets_operation_factory import (
    PrepareSearchTargetsOperationFactory,
)
from source.read_source_candidates_input import ReadSourceCandidatesInput
from source.read_source_candidates_operation_factory import (
    ReadSourceCandidatesOperationFactory,
)
from source.search_target_granularity import SearchTargetGranularity
from source.source_analysis_operation_factory import SourceAnalysisOperationFactory
from source.source_search_context import SourceSearchContext
from source.source_search_input import SourceSearchInput
from source.source_search_operation_factory import SourceSearchOperationFactory
from source.source_search_query import SourceSearchQuery

"""
solid-name: TestSourceCandidateAnalysisOperation
solid-category: integration-test
solid-spec: [SPEC-057]
solid-description: Verifies candidate analysis preserves prospective source authority and explicit unavailable evidence using real search, reads, and parsing.
"""


class TestSourceCandidateAnalysisOperation(TestCase):
    def setUp(self) -> None:
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        GitWorkingTreeFixture(self.root).initialize()
        self.path = self.root / "Reading.swift"
        self.path.write_text("protocol Reading { func read() }\n", encoding="utf-8")
        directory = ProjectDirectory(path=self.root)
        analyzer = SourceAnalysisOperationFactory().make(directory)
        self.operation = SourceCandidateAnalysisOperation(
            reader=ReadSourceCandidatesOperationFactory(directory).make(),
            analyzer=analyzer,
            candidate_visitor=CandidateSourceAnalysisVisitor(analyzer),
        )
        self.search = SourceSearchOperationFactory().make(directory)
        self.query = SourceSearchInput(
            queries=[SourceSearchQuery(id="interface", terms=["Reading"])]
        )

    def test_search_candidates_are_parsed_into_exact_declarations(self) -> None:
        found = self.search.execute(self.query)

        result = self.operation.execute(
            ReadSourceCandidatesInput(candidates=found.candidates)
        )

        self.assertEqual(len(result.analyses), 1)
        self.assertEqual(result.analyses[0].units[0].name, "Reading")
        self.assertEqual(result.analyses[0].units[0].members[0].name, "read")
        self.assertEqual(result.limitations, [])

    def test_duplicate_candidates_produce_one_source_analysis(self) -> None:
        found = self.search.execute(self.query)

        result = self.operation.execute(
            ReadSourceCandidatesInput(candidates=found.candidates * 2)
        )

        self.assertEqual(len(result.analyses), 1)

    def test_missing_candidate_records_a_limitation_instead_of_empty_compliance(
        self,
    ) -> None:
        found = self.search.execute(self.query)
        self.path.unlink()

        result = self.operation.execute(
            ReadSourceCandidatesInput(candidates=found.candidates)
        )

        self.assertEqual(result.analyses, [])
        self.assertEqual(len(result.limitations), 1)
        self.assertIn(str(self.path), result.limitations[0])

    def test_truncated_candidate_is_not_parsed_as_a_complete_declaration(self) -> None:
        found = self.search.execute(self.query)

        result = self.operation.execute(
            ReadSourceCandidatesInput(
                candidates=found.candidates,
                max_bytes_per_candidate=1,
            )
        )

        self.assertEqual(result.analyses, [])
        self.assertIn("inspection limit", result.limitations[0])

    def test_prospective_snapshot_remains_authoritative_after_disk_changes(
        self,
    ) -> None:
        prepared = (
            PrepareSearchTargetsOperationFactory()
            .make(ProjectDirectory(path=self.root))
            .execute(
                PrepareSearchTargetsInput(
                    source=FileAnalysisSource(path=self.path),
                    granularity=SearchTargetGranularity.UNIT,
                )
            )
        )
        found = self.search.execute(self.query)
        self.path.write_text("protocol Unrelated {}\n", encoding="utf-8")

        result = self.operation.execute(
            ReadSourceCandidatesInput(
                candidates=found.candidates,
                context=SourceSearchContext(sources=[prepared.snapshot]),
            )
        )

        self.assertEqual([unit.name for unit in result.analyses[0].units], ["Reading"])
        self.assertEqual(result.limitations, [])
