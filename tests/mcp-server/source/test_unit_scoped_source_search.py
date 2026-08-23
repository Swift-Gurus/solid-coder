"""Tests exact-unit exclusion during repository source search."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from source.read_source_candidates_input import ReadSourceCandidatesInput
from source.read_source_candidates_operation_factory import (
    ReadSourceCandidatesOperationFactory,
)
from source.prepare_search_query_input import PrepareSearchQueryInput
from source.prepare_search_query_operation import PrepareSearchQueryOperation
from source.exact_source_tokens_resolver_factory import (
    ExactSourceTokensResolverFactory,
)
from source.prepare_search_targets_input import PrepareSearchTargetsInput
from source.prepare_search_targets_operation_factory import (
    PrepareSearchTargetsOperationFactory,
)
from source.search_target_granularity import SearchTargetGranularity
from source.source_candidate_origin import SourceCandidateOrigin
from source.source_search_input import SourceSearchInput
from source.source_search_context import SourceSearchContext
from source.source_search_operation_factory import SourceSearchOperationFactory
from source.text_analysis_source import TextAnalysisSource
from hooks.pathlib_extractor import PathlibExtractor


"""
solid-name: TestUnitScopedSourceSearch
solid-category: integration-test
solid-spec: [SPEC-040]
solid-description: Proves repository search excludes only the reviewed unit while retaining and exactly loading sibling units from the same file.
"""
class TestUnitScopedSourceSearch(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project_root = Path(temporary.name)
        self.source_path = self.project_root / "Sources" / "Calculators.swift"
        self.source_path.parent.mkdir(parents=True)
        self.source_path.write_text(
            """struct PrimaryCalculator {
    func sharedCalculation() -> Int { 1 }
}

struct SiblingCalculator {
    func sharedCalculation() -> Int { 2 }
}
""",
            encoding="utf-8",
        )
        self.query_preparer = PrepareSearchQueryOperation(
            tokens=ExactSourceTokensResolverFactory().make(),
            extension=PathlibExtractor(
                lambda path: Path(path).suffix.lower()
            ),
        )

    def test_excludes_only_reviewed_unit_and_loads_exact_sibling_source(self) -> None:
        prospective_buffer = self.source_path.read_text(encoding="utf-8").replace(
            "sharedCalculation() -> Int { 1 }",
            "sharedCalculation() -> Int { 99 }",
        )
        targets = PrepareSearchTargetsOperationFactory().make().execute(
            PrepareSearchTargetsInput(
                source=TextAnalysisSource(
                    text=prospective_buffer,
                    virtual_path=str(self.source_path),
                ),
                granularity=SearchTargetGranularity.UNIT,
            )
        ).targets
        reviewed = next(
            target for target in targets if target.name == "PrimaryCalculator"
        )
        query = self.query_preparer.execute(
            PrepareSearchQueryInput(
                target=reviewed,
                generated_terms=["sharedCalculation"],
            )
        )
        searched = SourceSearchOperationFactory().make(
            lambda: self.project_root,
            SearchTargetGranularity.UNIT,
        ).execute(
            SourceSearchInput(
                queries=query.queries,
                excluded_units=query.excluded_units,
            )
        )

        same_file = [
            candidate
            for candidate in searched.candidates
            if candidate.path == self.source_path.resolve()
        ]
        self.assertEqual(len(same_file), 1)
        self.assertEqual(
            same_file[0].unit_identity,
            "struct:SiblingCalculator:5",
        )

        loaded = ReadSourceCandidatesOperationFactory(
            lambda: self.project_root
        ).make().execute(
            ReadSourceCandidatesInput(
                candidates=same_file,
            )
        ).results[0]
        self.assertEqual(
            loaded.content,
            "struct SiblingCalculator {\n"
            "    func sharedCalculation() -> Int { 2 }\n"
            "}",
        )
        self.assertNotIn("PrimaryCalculator", loaded.content)

    def test_proposed_sibling_replaces_the_stale_disk_candidate(self) -> None:
        prospective_buffer = self.source_path.read_text(encoding="utf-8").replace(
            "sharedCalculation() -> Int { 2 }",
            "sharedCalculation() -> Int { 77 }",
        )
        prepared = PrepareSearchTargetsOperationFactory().make().execute(
            PrepareSearchTargetsInput(
                source=TextAnalysisSource(
                    text=prospective_buffer,
                    virtual_path=str(self.source_path),
                ),
                granularity=SearchTargetGranularity.UNIT,
            )
        )
        reviewed = next(
            target for target in prepared.targets
            if target.name == "PrimaryCalculator"
        )
        query = self.query_preparer.execute(
            PrepareSearchQueryInput(
                target=reviewed,
                generated_terms=["sharedCalculation"],
            )
        )
        searched = SourceSearchOperationFactory().make(
            lambda: self.project_root,
            SearchTargetGranularity.UNIT,
        ).execute(SourceSearchInput(
            queries=query.queries,
            excluded_units=query.excluded_units,
            context=SourceSearchContext(sources=[prepared.snapshot]),
        ))

        self.assertEqual(len(searched.candidates), 1)
        candidate = searched.candidates[0]
        self.assertEqual(candidate.origin, SourceCandidateOrigin.PROPOSED)
        loaded = ReadSourceCandidatesOperationFactory(
            lambda: self.project_root
        ).make().execute(ReadSourceCandidatesInput(
            candidates=[candidate],
            context=SourceSearchContext(sources=[prepared.snapshot]),
        )).results[0]
        self.assertIn("Int { 77 }", loaded.content)
        self.assertNotIn("Int { 2 }", loaded.content)

    def test_searches_units_from_another_proposed_patch_file(self) -> None:
        first = PrepareSearchTargetsOperationFactory().make().execute(
            PrepareSearchTargetsInput(
                source=TextAnalysisSource(
                    text="struct FirstFormatter { func formatProfile() {} }",
                    virtual_path=str(self.project_root / "FirstFormatter.swift"),
                ),
                granularity=SearchTargetGranularity.UNIT,
            )
        )
        second_path = self.project_root / "SecondFormatter.swift"
        second_path.write_text(
            "struct StaleFormatter { func unrelated() {} }",
            encoding="utf-8",
        )
        second = PrepareSearchTargetsOperationFactory().make().execute(
            PrepareSearchTargetsInput(
                source=TextAnalysisSource(
                    text=(
                        "struct SecondFormatter { "
                        "func formatProfile() {} }"
                    ),
                    virtual_path=str(second_path),
                ),
                granularity=SearchTargetGranularity.UNIT,
            )
        )
        query = self.query_preparer.execute(
            PrepareSearchQueryInput(
                target=first.targets[0],
                generated_terms=["formatProfile"],
            )
        )

        searched = SourceSearchOperationFactory().make(
            lambda: self.project_root,
            SearchTargetGranularity.UNIT,
        ).execute(SourceSearchInput(
            queries=query.queries,
            excluded_units=query.excluded_units,
            context=SourceSearchContext(
                sources=[first.snapshot, second.snapshot]
            ),
        ))

        proposed = [
            candidate
            for candidate in searched.candidates
            if candidate.origin is SourceCandidateOrigin.PROPOSED
        ]
        self.assertEqual([candidate.unit for candidate in proposed], ["SecondFormatter"])
        self.assertFalse(
            any(candidate.unit == "StaleFormatter" for candidate in searched.candidates)
        )


if __name__ == "__main__":
    unittest.main()
