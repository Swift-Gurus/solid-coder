"""Exercises multi-term search through both production entry points."""

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "harness" / "flow_engine"))

from git_working_tree_fixture import GitWorkingTreeFixture
from harness.project_context import ProjectDirectory
from health.dry_search_completion_status import DrySearchCompletionStatus
from health.dry_search_service_factory import DrySearchServiceFactory
from operation_workflow_integration_driver import OperationWorkflowIntegrationDriver
from search.codebase_search_executor_factory import CodebaseSearchExecutorFactory
from search.codebase_search_output_renderer import CodebaseSearchOutputRenderer
from search.codebase_search_query_kind import CodebaseSearchQueryKind
from search.codebase_searcher_factory import CodebaseSearcherFactory
from source.analysis.tree_sitter_syntax_parser import TreeSitterSyntaxParser
from source.source_operation_registrations_factory import (
    SourceOperationRegistrationsFactory,
)
from source.source_search_input import SourceSearchInput
from source.source_search_query import SourceSearchQuery

"""
solid-name: TestSharedSourceSearchEntryPoints
solid-category: integration-test
solid-spec: [SPEC-040, SPEC-060]
solid-description: Exercises shared multi-term search through legacy health completion and engine-owned workflow execution with persisted replay.
"""


class TestSharedSourceSearchEntryPoints(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.project = self.root / "project"
        self.path = self.project / "Sources" / "Catalog.swift"
        self.path.parent.mkdir(parents=True)
        GitWorkingTreeFixture(self.project).initialize()
        self.path.write_text(
            "// solid-name: Catalog\n"
            "// solid-description: Retrieves profile records.\n"
            "struct Catalog { func loadProfile() {} }\n",
            encoding="utf-8",
        )
        excluded = self.project / "Tuist" / ".build" / "HiddenProfile.swift"
        excluded.parent.mkdir(parents=True)
        excluded.write_text("struct HiddenProfile {}\n", encoding="utf-8")
        self.health_output = self.root / "health"
        self.health_output.mkdir()
        (self.health_output / "hook-input.json").write_text("{}\n", encoding="utf-8")
        self.query = SourceSearchQuery(
            id="profile",
            terms=["profile", *[f"absent{index}" for index in range(37)]],
        )
        self.health_services = DrySearchServiceFactory()
        self.legacy = self.health_services.make_search(
            CodebaseSearcherFactory().make(ProjectDirectory(path=self.project))
        )
        workflow_root = self.root / "workflow"
        workflow_root.mkdir()
        registrations = SourceOperationRegistrationsFactory(
            ProjectDirectory(path=self.project),
        ).make()
        self.search = next(
            entry.handler for entry in registrations if entry.name == "source.search"
        )
        self.driver = OperationWorkflowIntegrationDriver(
            project_root=workflow_root,
            registrations=registrations,
        )
        self.expected = (
            "Here is what we found:\n\ncandidate_id: candidate-1\nunit: Catalog\n"
            f"description: Retrieves profile records.\npath: {self.path.resolve()}"
        )

    def test_legacy_search_returns_candidate_and_records_dry_completion(self) -> None:
        result = self.legacy.search(
            sources_dir=str(self.project),
            tags=self.query.terms,
            output_dir=str(self.health_output),
        )

        self.assertEqual(result, self.expected)
        self.assertEqual(
            self.health_services.make_completion_store().status(
                str(self.health_output)
            ),
            DrySearchCompletionStatus.COMPLETE,
        )

    def test_registered_workflow_search_replays_original_result_after_file_changes(
        self,
    ) -> None:
        self.driver.write_workflow(
            textwrap.dedent("""
            id: shared-source-search
            name: Shared Source Search
            max_turns: 5
            steps:
              - id: search
                type: operation
                operation: source.search
                with:
                  queries: "{{params.queries}}"
                  included_file_extensions: "{{params.extensions}}"
              - id: present
                type: operation
                operation: source.present_search
                depends_on: [search]
                with:
                  candidates: "{{steps.search.outputs.candidates}}"
                  files_scanned: "{{steps.search.outputs.files_scanned}}"
              - id: report
                depends_on: [present]
                prompt: "{{steps.present.outputs.text}}"
        """)
        )

        started = self.driver.start(
            params={
                "queries": [self.query.model_dump(mode="json")],
                "extensions": [".swift"],
            }
        )
        self.path.write_text("struct Changed {}\n", encoding="utf-8")
        replayed = self.driver.advance()
        completed = self.driver.advance({started.steps[0].instance_id: {}})

        self.assertEqual(started.steps[0].prompt, self.expected)
        self.assertEqual(replayed.steps[0].prompt, self.expected)
        self.assertEqual(completed.status, "done")

    def test_both_entry_points_publish_identical_metadata_and_undocumented_candidates(
        self,
    ) -> None:
        (self.project / "Sources" / "Plain.swift").write_text(
            "struct FirstProfile {}\nstruct SecondProfile {}\n",
            encoding="utf-8",
        )

        legacy = self.legacy.search(
            sources_dir=str(self.project), tags=self.query.terms
        )
        workflow = self.search.execute(
            SourceSearchInput(
                queries=[self.query],
                max_candidates=100,
            )
        )
        presented = CodebaseSearchOutputRenderer().render(workflow, self.project)

        self.assertEqual(legacy, presented)
        self.assertIn("unit: Plain.swift", presented)
        self.assertIn("description: No solid-description frontmatter.", presented)

    def test_search_does_not_invoke_swift_parser_even_for_matching_source(self) -> None:
        (self.project / "Sources" / "Plain.swift").write_text(
            "struct UndocumentedProfile {}\n"
        )
        (self.project / "Sources" / "Unrelated.swift").write_text(
            "struct Unrelated {}\n"
        )
        with patch.object(
            TreeSitterSyntaxParser,
            "parse",
            side_effect=AssertionError("Search must not parse Swift"),
        ) as parser:
            legacy = self.legacy.search(
                sources_dir=str(self.project), tags=self.query.terms
            )
            workflow = self.search.execute(SourceSearchInput(queries=[self.query]))

        parser.assert_not_called()
        self.assertEqual(
            [candidate.unit for candidate in workflow.candidates],
            ["Catalog", "Plain.swift"],
        )
        self.assertEqual(
            CodebaseSearchOutputRenderer().render(workflow, self.project), legacy
        )

    def test_equivalent_inputs_preserve_identical_typed_provenance_and_order(
        self,
    ) -> None:
        legacy = (
            CodebaseSearchExecutorFactory()
            .make(ProjectDirectory(path=self.project))
            .execute(
                sources_dir=str(self.project),
                plan_path=None,
                tags=self.query.terms,
                spec_numbers=None,
                min_matches=1,
            )
        )
        workflow = self.search.execute(
            SourceSearchInput(
                queries=[
                    SourceSearchQuery(
                        id=CodebaseSearchQueryKind.TERMS.value, terms=self.query.terms
                    )
                ],
                max_candidates=100,
            )
        )

        self.assertEqual(legacy.output, workflow)

    def test_candidates_do_not_claim_declaration_ranges(self) -> None:
        candidate = self.search.execute(
            SourceSearchInput(queries=[self.query])
        ).candidates[0]

        self.assertNotIn("start_offset", candidate.model_dump())
        self.assertNotIn("end_offset", candidate.model_dump())
