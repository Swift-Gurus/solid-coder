"""Exercises repository-backed LSP relationship classification."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))

from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory  # noqa: E402
from harness.project_context import ProjectDirectory  # noqa: E402
from harness.rule_applicability_context import RuleApplicabilityContext  # noqa: E402
from harness.runs_base_dir_resolver import RunsBaseDirResolver  # noqa: E402
from harness.static_session_id_reader import StaticSessionIdReader  # noqa: E402
from review.normalized_review_unit import NormalizedReviewUnit  # noqa: E402
from source.file_analysis_source import FileAnalysisSource  # noqa: E402
from source.prepare_search_targets_input import PrepareSearchTargetsInput  # noqa: E402
from source.prepare_search_targets_operation_factory import (  # noqa: E402
    PrepareSearchTargetsOperationFactory,
)
from source.search_target_granularity import SearchTargetGranularity  # noqa: E402
from source.selected_source_candidate import SelectedSourceCandidate  # noqa: E402
from source.source_operation_registrations_factory import (  # noqa: E402
    SourceOperationRegistrationsFactory,
)
from source.source_search_context import SourceSearchContext  # noqa: E402


"""
solid-name: TestLSPRepositoryRelationshipFlow
solid-category: integration-test
solid-spec: [SPEC-057]
solid-description: Verifies LSP searches, inspects, classifies, and deterministically counts concrete inheritance violations.
"""
class TestLSPRepositoryRelationshipFlow(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.run_root = Path(temporary.name)
        self.project_directory = ProjectDirectory(path=self.run_root)
        fixture = (
            _PROJECT_ROOT
            / "tests"
            / "principles"
            / "LSP"
            / "fixtures"
            / "fixture-3.swift"
        )
        prepared = PrepareSearchTargetsOperationFactory().make().execute(
            PrepareSearchTargetsInput(
                source=FileAnalysisSource(path=fixture),
                granularity=SearchTargetGranularity.UNIT,
            )
        )
        target = next(
            candidate
            for candidate in prepared.targets
            if candidate.name == "NonEmptyRequestProcessor"
        )
        self.params = {
            "review_unit": NormalizedReviewUnit(
                target=target,
                applicability=RuleApplicabilityContext(
                    file_extension=".swift",
                    unit_kind="class",
                    tags=[],
                ),
                tag_evidence=[],
            ).model_dump(mode="json"),
            "source_context": SourceSearchContext(
                sources=[prepared.snapshot]
            ).model_dump(mode="json"),
        }
        self.sut = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.run_root
            ),
            plugin_root=_PROJECT_ROOT,
            project_directory=self.project_directory,
            session_reader=StaticSessionIdReader("spec-057-lsp-repository"),
            operation_registrations=SourceOperationRegistrationsFactory(
                project_directory=self.project_directory,
            ).make(),
        ).build()

    def test_counts_classified_relationship_violations_without_model_arithmetic(
        self,
    ) -> None:
        started = self.sut.flow_start("lsp", self.params)
        analysis = started.steps[0]
        selection = self.sut.flow_next({
            analysis.instance_id: {
                "type_checks": [],
                "has_inheritance": True,
                "relationship_terms": ["RequestProcessor"],
                "contract_implementations": [],
            }
        })
        self.assertEqual(
            [step.step_id for step in selection.steps],
            ["select_relationship_candidates"],
        )
        candidate_ids = self._presented_candidate_ids(started.run_id)
        inspections = self.sut.flow_next({
            selection.steps[0].instance_id: {
                "dispositions": [
                    {
                        "candidate_id": candidate_id,
                        "disposition": "INSPECT",
                        "reasoning": "The candidate may be the concrete base.",
                        "evidence": "Its declaration name matches the base type.",
                    }
                    for candidate_id in candidate_ids
                ]
            }
        })
        self.assertEqual(len(inspections.steps), 1)
        selected = self._selected_candidates(started.run_id)
        classifications = self.sut.flow_next({
            inspections.steps[0].instance_id: {
                "reasoning": "Read the selected base declaration.",
                "evidence": f"Read {selected[0].source.path}.",
            }
        })
        normalized = self.sut.flow_next({
            classifications.steps[0].instance_id: {
                "assessment": {
                    "candidate_id": selected[0].candidate_id,
                    "location": str(selected[0].source.path),
                    "name": selected[0].source.unit,
                    "classification": "BASE_DECLARATION",
                    "violations": [
                        {
                            "classification": "NEW_GUARD",
                            "member": "process",
                            "is_exception": False,
                            "reasoning": "The subtype rejects an input accepted by the base.",
                            "evidence": "NonEmptyRequestProcessor adds !request.isEmpty.",
                        }
                    ],
                    "reasoning": "The declaration is the inspected concrete base.",
                    "evidence": "RequestProcessor declares process(_:).",
                }
            }
        })
        self.assertEqual(
            [step.step_id for step in normalized.steps],
            ["classify_relationship_violations"],
        )
        exception = self.sut.flow_next({
            normalized.steps[0].instance_id: {
                "observations": [
                    {
                        "candidate_id": selected[0].candidate_id,
                        "classification": "NEW_GUARD",
                        "member": "process",
                        "is_exception": False,
                        "reasoning": "The completed comparison found a stronger precondition.",
                        "evidence": "NonEmptyRequestProcessor adds !request.isEmpty.",
                    }
                ]
            }
        })

        self.assertEqual(
            [step.step_id for step in exception.steps],
            ["classify_exception"],
        )
        metric = next(
            event
            for event in self._events(started.run_id)
            if event.get("event") == "step_completed"
            and event.get("step_id") == "contract_violations"
        )
        self.assertEqual(metric["outputs"]["value"], 1)
        self.assertIsNotNone(metric["metric_derivation"])

    def _presented_candidate_ids(self, run_id: str) -> list[str]:
        event = next(
            event
            for event in self._events(run_id)
            if event.get("event") == "step_completed"
            and event.get("step_id") == "search_relationship_candidates"
        )
        return [
            f"candidate-{index}"
            for index, _ in enumerate(event["outputs"]["candidates"], start=1)
        ]

    def _selected_candidates(self, run_id: str) -> list[SelectedSourceCandidate]:
        event = next(
            event
            for event in self._events(run_id)
            if event.get("event") == "step_completed"
            and event.get("step_id") == "validate_relationship_candidates"
        )
        return [
            SelectedSourceCandidate.model_validate(candidate)
            for candidate in event["outputs"]["selected_candidates"]
        ]

    def _events(self, run_id: str) -> list[dict[str, object]]:
        return [
            json.loads(line)
            for line in (
                self.run_root / "runs" / run_id / "events.jsonl"
            ).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]


if __name__ == "__main__":
    unittest.main()
