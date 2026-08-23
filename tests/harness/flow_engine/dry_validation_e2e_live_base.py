"""Defines the backend-neutral live DRY workflow assertions."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parents[1]
_MCP_SERVER = Path(__file__).resolve().parents[3] / "mcp-server"
for _directory in (_HARNESS_DIR, _MCP_SERVER):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

from dry_candidate_assessment import DRYCandidateAssessment  # noqa: E402
from dry_repository_scenario_expectation import (  # noqa: E402
    DRYRepositoryScenarioExpectation,
)
from dry_rule_workflow_parameters import DRYRuleWorkflowParameters  # noqa: E402
from live_rule_validation_expectation import (  # noqa: E402
    LiveRuleValidationExpectation,
)
from live_session_artifact_scope import LiveSessionArtifactScope  # noqa: E402
from live_workflow_scenario import LiveWorkflowScenario  # noqa: E402
from preserved_live_workflow_run import PreservedLiveWorkflowRun  # noqa: E402
from rule_validation_e2e_live_base import RuleValidationE2ELiveBase  # noqa: E402
from harness.rule_applicability_context import RuleApplicabilityContext  # noqa: E402
from review.normalized_review_unit import NormalizedReviewUnit  # noqa: E402
from source.file_analysis_source import FileAnalysisSource  # noqa: E402
from source.prepare_search_targets_input import PrepareSearchTargetsInput  # noqa: E402
from source.prepare_search_targets_operation_factory import (  # noqa: E402
    PrepareSearchTargetsOperationFactory,
)
from source.search_target_granularity import SearchTargetGranularity  # noqa: E402
from source.source_search_candidate import SourceSearchCandidate  # noqa: E402
from source.source_search_context import SourceSearchContext  # noqa: E402


_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_FIXTURE = _PROJECT_ROOT / "tests" / "principles" / "DRY" / "fixtures" / "fixture-1.swift"
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
solid-spec: [SPEC-039, SPEC-040]
solid-description: Supplies an isolated unit-scoped DRY scenario and exact operation, observation, scoring, and audit assertions.
"""
class DRYValidationE2ELiveBase(RuleValidationE2ELiveBase):
    WORKFLOW_ID = "dry"
    ARTIFACT_SCENARIO = "dry"
    FIXTURE = _FIXTURE
    EXPECTED_STEP_IDS = [
        "reuse_misses",
        "duplicate_sites",
        "missing_abstractions",
    ]
    EXPECTED_METRIC_IDS = ["DRY-1", "DRY-2", "DRY-3"]
    EXPECTED_VALUES = [0, 2, 1]
    EXPECTED_METRIC_SEVERITIES = ["COMPLIANT", "SEVERE", "SEVERE"]
    EXPECTED_FINAL_SEVERITY = "SEVERE"
    ALLOW_AUXILIARY_STEPS = True

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="solid-coder-dry-live-")
        self.addCleanup(temporary.cleanup)
        self._execution_root = Path(temporary.name)
        self._reviewed_source = self._execution_root / "PayrollLedger.swift"
        self._reviewed_source.write_text(
            self.FIXTURE.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        super().setUp()

    @property
    def execution_project_root(self) -> Path:
        return self._execution_root

    @property
    def workflow_parameters(self) -> DRYRuleWorkflowParameters:
        prepared = PrepareSearchTargetsOperationFactory().make().execute(
            PrepareSearchTargetsInput(
                source=FileAnalysisSource(path=self._reviewed_source),
                granularity=SearchTargetGranularity.UNIT,
            )
        )
        self.assertEqual(len(prepared.targets), 1)
        target = prepared.targets[0]
        return DRYRuleWorkflowParameters(
            review_unit=NormalizedReviewUnit(
                target=target,
                applicability=RuleApplicabilityContext(
                    file_extension=".swift",
                    unit_kind=target.kind,
                    tags=[],
                ),
                tag_evidence=[],
            ),
            source_context=SourceSearchContext(sources=[prepared.snapshot]),
        )

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
        classified = self._completion(completions, "classify_candidate")

        self.assertTrue(generated["outputs"]["generated_terms"])
        self.assertEqual(searched["outputs"]["candidates"], [])
        self.assertEqual(selected["outputs"]["selections"], [])
        self.assertEqual(validated["outputs"]["selected_candidates"], [])
        self.assertEqual(classified["outputs"]["assessment"], [])
        self.assertTrue(classified["empty_collection"])
        self.assertEqual(searched["session_id"], "engine")
        self.assertEqual(validated["session_id"], "engine")
        self.assertEqual(classified["session_id"], "engine")

    def test_existing_protocol_with_different_names_is_an_exact_reuse_miss(
        self,
    ) -> None:
        self._provision_protocol_reuse_scenario()
        expectation = DRYRepositoryScenarioExpectation.model_validate_json(
            (_PROTOCOL_REUSE_SCENARIO / "expectation.json").read_text(
                encoding="utf-8"
            )
        )
        run = self._run_scenario(LiveWorkflowScenario(
            workflow_id=self.WORKFLOW_ID,
            parameters=self.workflow_parameters,
            artifact_scope=LiveSessionArtifactScope(
                domain="review",
                scenario="dry-exact-protocol-reuse",
            ),
        ))

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
        temporary = tempfile.TemporaryDirectory(prefix="solid-coder-dry-reuse-live-")
        self.addCleanup(temporary.cleanup)
        self._execution_root = Path(temporary.name)
        self._reviewed_source = self._execution_root / "NetworkResourceFetching.swift"
        self._reviewed_source.write_text(
            (_PROTOCOL_REUSE_SCENARIO / "reviewed.swift").read_text(
                encoding="utf-8"
            ),
            encoding="utf-8",
        )
        (self._execution_root / "RemoteContentLoading.swift").write_text(
            (_PROTOCOL_REUSE_SCENARIO / "existing.swift").read_text(
                encoding="utf-8"
            ),
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
                for line in (run.run_directory / "events.jsonl").read_text().splitlines()
                if line.strip()
            )
            if event.get("event") == "step_completed"
        ]
        classification = self._completion(completions, "classify_candidate")
        candidate = SourceSearchCandidate.model_validate(classification["item"])
        assessment = DRYCandidateAssessment.model_validate(
            classification["outputs"]["assessment"]
        )

        self.assertEqual(candidate.unit, expectation.candidate_name)
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
