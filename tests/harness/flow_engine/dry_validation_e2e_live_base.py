"""Defines the backend-neutral live DRY workflow assertions."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import ClassVar

_HARNESS_DIR = Path(__file__).resolve().parents[1]
_MCP_SERVER = Path(__file__).resolve().parents[3] / "mcp-server"
for _directory in (_HARNESS_DIR, _MCP_SERVER):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

from dry_candidate_assessment import DRYCandidateAssessment
from dry_repository_scenario_expectation import (
    DRYRepositoryScenarioExpectation,
)
from live_rule_validation_expectation import (
    LiveRuleValidationExpectation,
)
from live_session_artifact_scope import LiveSessionArtifactScope
from live_workflow_scenario import LiveWorkflowScenario
from preserved_live_workflow_run import PreservedLiveWorkflowRun
from rule_validation_e2e_live_base import RuleValidationE2ELiveBase
from source.selected_source_candidate import SelectedSourceCandidate

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_FIXTURE = (
    _PROJECT_ROOT / "tests" / "principles" / "DRY" / "fixtures" / "fixture-1.swift"
)
_PROTOCOL_REUSE_SCENARIO = (
    _PROJECT_ROOT
    / "tests"
    / "principles"
    / "DRY"
    / "repository-scenarios"
    / "exact-protocol-reuse"
)


"""
solid-name: DRYValidationE2ELiveBase
solid-category: test-support
solid-spec: [SPEC-039, SPEC-040, SPEC-056]
solid-description: Supplies an isolated unit-scoped DRY scenario and exact operation, observation, scoring, and audit assertions.
"""


class DRYValidationE2ELiveBase(RuleValidationE2ELiveBase):
    WORKFLOW_ID = "dry"
    ARTIFACT_SCENARIO = "dry"
    FIXTURE = _FIXTURE
    EXPECTED_STEP_IDS: ClassVar[list[str]] = [
        "reuse_misses",
        "repository_duplicate_sites",
        "within_unit_duplicate_sites",
    ]
    EXPECTED_METRIC_IDS: ClassVar[list[str]] = ["DRY-1", "DRY-2", "DRY-2"]
    EXPECTED_OBSERVATION_IDS: ClassVar[list[str]] = [
        "repository_reuse_miss_count",
        "repository_duplicate_location_count",
        "within_unit_duplicate_location_count",
    ]
    EXPECTED_VALUES: ClassVar[list[int]] = [0, 0, 2]
    EXPECTED_METRIC_SEVERITIES: ClassVar[list[str]] = [
        "COMPLIANT",
        "COMPLIANT",
        "SEVERE",
    ]
    EXPECTED_FINAL_SEVERITY = "SEVERE"
    ALLOW_AUXILIARY_STEPS = True

    def setUp(self) -> None:
        super().setUp()
        for candidate in (self._source_project.root / "Sources" / "Candidates").glob(
            "*.swift"
        ):
            candidate.unlink()

    def assert_workflow(self, run) -> None:
        super().assert_workflow(run)
        events = [
            json.loads(line)
            for line in (run.run_directory / "events.jsonl").read_text().splitlines()
            if line.strip()
        ]
        completions = [
            event for event in events if event.get("event") == "step_completed"
        ]
        generated = self._completion(completions, "generate_terms")
        searched = self._completion(completions, "search_repository")
        selected = self._completion(completions, "select_candidates")
        validated = self._completion(completions, "validate_selection")
        target_analysis = self._completion(completions, "analyze_target_patterns")

        self.assertTrue(generated["outputs"]["generated_terms"])
        self.assertEqual(searched["outputs"]["candidates"], [])
        self.assertEqual(selected["outputs"]["dispositions"], [])
        self.assertEqual(validated["outputs"]["selected_candidates"], [])
        self.assertEqual(validated["outputs"]["dispositions"], [])
        self.assertFalse(
            any(
                str(event.get("step_id", "")).endswith("classify_candidate")
                for event in completions
            )
        )
        self.assertEqual(
            bool(target_analysis["outputs"]["within_unit_duplicates"]),
            self.EXPECTED_VALUES[2] > 0,
        )
        self.assertNotIn("missing_abstractions", target_analysis["outputs"])
        self.assertEqual(searched["session_id"], "engine")
        self.assertEqual(validated["session_id"], "engine")
        for step_id in self.EXPECTED_STEP_IDS:
            self.assertEqual(
                self._completion(completions, step_id)["session_id"],
                "engine",
            )

    def test_rounding_variation_exposes_shared_calculation(self) -> None:
        self._assert_fixture_scenario(
            _FIXTURE.with_name("fixture-3.swift"),
            "dry-rounding-variation",
        )

    def test_identical_wrappers_are_duplicate_sites(self) -> None:
        self._assert_fixture_scenario(
            _FIXTURE.with_name("fixture-2.swift"),
            "dry-extracted-helper",
        )

    def _assert_fixture_scenario(self, fixture: Path, artifact_scenario: str) -> None:
        self.FIXTURE = fixture
        self.ARTIFACT_SCENARIO = artifact_scenario
        self._source_project.review_target.write_text(
            fixture.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        self.assert_workflow(self._run_scenario(self.scenario))

    def test_existing_protocol_with_different_names_is_an_exact_reuse_miss(
        self,
    ) -> None:
        self._provision_protocol_reuse_scenario()
        expectation = DRYRepositoryScenarioExpectation.model_validate_json(
            (_PROTOCOL_REUSE_SCENARIO / "expectation.json").read_text(encoding="utf-8")
        )
        run = self._run_scenario(
            LiveWorkflowScenario(
                workflow_id=self.REVIEW_WORKFLOW_ID,
                parameters=self.workflow_parameters,
                artifact_scope=LiveSessionArtifactScope(
                    domain="review",
                    scenario="dry-exact-protocol-reuse",
                ),
                model_context=(
                    "Source under review:\n"
                    "```swift\n"
                    f"{self._source_project.review_target.read_text(encoding='utf-8')}"
                    "\n```"
                ),
            )
        )

        self.assert_rule_workflow(
            run,
            LiveRuleValidationExpectation(
                workflow_id=self.WORKFLOW_ID,
                metrics=expectation.metrics,
                final_severity=expectation.severity,
                is_exception=expectation.is_exception,
                allow_auxiliary_steps=True,
            ),
        )
        self._assert_candidate_classification(run, expectation)

    def _provision_protocol_reuse_scenario(self) -> None:
        self._source_project.review_target.write_text(
            (_PROTOCOL_REUSE_SCENARIO / "reviewed.swift").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (
            self._source_project.review_target.parent / "RemoteContentLoading.swift"
        ).write_text(
            (_PROTOCOL_REUSE_SCENARIO / "existing.swift").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    def _assert_candidate_classification(
        self,
        run: PreservedLiveWorkflowRun,
        expectation: DRYRepositoryScenarioExpectation,
    ) -> None:
        completions = [
            event
            for event in (
                json.loads(line)
                for line in (run.run_directory / "events.jsonl")
                .read_text()
                .splitlines()
                if line.strip()
            )
            if event.get("event") == "step_completed"
        ]
        classification = self._completion(completions, "classify_candidate")
        selected = SelectedSourceCandidate.model_validate(classification["item"])
        assessment = DRYCandidateAssessment.model_validate(
            classification["outputs"]["assessment"]
        )

        self.assertEqual(selected.source.unit, expectation.candidate_name)
        self.assertEqual(assessment.candidate_id, selected.candidate_id)
        self.assertEqual(assessment.location, str(selected.source.path))
        self.assertEqual(
            assessment.reuse.classification,
            expectation.reuse_classification,
        )
        self.assertEqual(
            assessment.duplication.classification,
            expectation.duplication_classification,
        )

    def _completion(
        self,
        completions: list[dict[str, object]],
        step_suffix: str,
    ) -> dict[str, object]:
        return next(
            event
            for event in completions
            if str(event["step_id"]).endswith(step_suffix)
        )
