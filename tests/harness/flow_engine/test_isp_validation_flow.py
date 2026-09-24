"""
solid-name: test_isp_validation_flow
solid-category: integration-test
solid-spec: [SPEC-039]
solid-description: Verifies canonical ISP instructions, protocol applicability, typed observations, exception handling, scoring, and audit behavior.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_HARNESS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))
sys.path.insert(0, str(_HARNESS))

from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory  # noqa: E402
from harness.rule_applicability_context import RuleApplicabilityContext  # noqa: E402
from harness.runs_base_dir_resolver import RunsBaseDirResolver  # noqa: E402
from harness.static_session_id_reader import StaticSessionIdReader  # noqa: E402
from isp_rule_workflow_parameters import ISPRuleWorkflowParameters  # noqa: E402
from review.normalized_review_unit import NormalizedReviewUnit  # noqa: E402
from rule_analysis_expectation import RuleAnalysisExpectation  # noqa: E402
from rule_metric_expectation import RuleMetricExpectation  # noqa: E402
from rule_validation_flow_contract import RuleValidationFlowContract  # noqa: E402
from rule_validation_scenario import RuleValidationScenario  # noqa: E402
from rule_workflow_checkpoint import RuleWorkflowCheckpoint  # noqa: E402
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


class TestISPValidationFlow(RuleValidationFlowContract):
    __test__ = True
    PROJECT_ROOT = _PROJECT_ROOT
    SCENARIO = RuleValidationScenario(
        workflow_id="isp",
        rule_path=_PROJECT_ROOT / "references" / "principles" / "ISP" / "rule.md",
        fixture_path=(
            _PROJECT_ROOT
            / "tests"
            / "principles"
            / "ISP"
            / "fixtures"
            / "fixture-1.swift"
        ),
        analysis=[
            RuleAnalysisExpectation(
                step_id="analyze_protocol",
                output={},
            ),
            RuleAnalysisExpectation(
                step_id="select_candidates",
                output={},
            ),
            *(
                RuleAnalysisExpectation(
                    step_id=f"candidate_reviews-{index}.inspect_candidate",
                    output={},
                )
                for index in range(1, 4)
            ),
            *(
                RuleAnalysisExpectation(
                    step_id=f"candidate_reviews-{index}.classify_candidate",
                    output={},
                )
                for index in range(1, 4)
            ),
            *(
                RuleAnalysisExpectation(
                    step_id=(
                        f"candidate_reviews-{index}."
                        "classify_requirement_coverage"
                    ),
                    output={},
                )
                for index in range(1, 4)
            ),
            RuleAnalysisExpectation(
                step_id="analyze_cohesion",
                output={},
            ),
        ],
        metrics=[
            RuleMetricExpectation(
                step_id="width",
                metric_id="ISP-1",
                detection_id="ISP-1",
                detection_name="Protocol Width",
                value=10,
                severity="SEVERE",
                mcp_owned=True,
            ),
            RuleMetricExpectation(
                step_id="min_coverage",
                metric_id="ISP-2",
                detection_id="ISP-2",
                detection_name="Conformer Coverage",
                value=0.5,
                severity="SEVERE",
                mcp_owned=True,
            ),
            RuleMetricExpectation(
                step_id="cohesion_groups",
                metric_id="ISP-3",
                detection_id="ISP-3",
                detection_name="Protocol Cohesion Groups",
                value=2,
                severity="SEVERE",
                mcp_owned=True,
            ),
        ],
        final_severity="SEVERE",
        included_unit_kinds=["protocol"],
    )

    def setUp(self) -> None:
        super().setUp()
        prepared = PrepareSearchTargetsOperationFactory().make().execute(
            PrepareSearchTargetsInput(
                source=FileAnalysisSource(path=self.SCENARIO.fixture_path),
                granularity=SearchTargetGranularity.UNIT,
            )
        )
        protocol = next(
            target for target in prepared.targets
            if target.kind == "protocol"
        )
        self.review_unit = "protocol DocumentService {"
        self.review_unit_name = protocol.name
        self._parameters = ISPRuleWorkflowParameters(
            review_unit=NormalizedReviewUnit(
                target=protocol,
                applicability=RuleApplicabilityContext(
                    file_extension=".swift",
                    unit_kind="protocol",
                    tags=[],
                ),
                tag_evidence=[],
            ),
            source_context=SourceSearchContext(sources=[prepared.snapshot]),
        )
        self.sut = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.project_root
            ),
            plugin_root=self.PROJECT_ROOT,
            session_reader=StaticSessionIdReader("spec-039-isp-test"),
            operation_registrations=SourceOperationRegistrationsFactory(
                project_directory=self.project_directory,
            ).make(),
        ).build()

    def _start(self):
        return self.sut.flow_start(
            self.SCENARIO.workflow_id,
            self._parameters.model_dump(mode="json"),
        )

    def test_repository_evidence_is_reduced_without_model_owned_metrics(self) -> None:
        checkpoint = self._advance_through_analysis()

        self.assertEqual(
            [step.step_id for step in checkpoint.result.steps],
            ["classify_exception"],
        )
        prompts = "\n".join(checkpoint.prompts)
        self.assertIn("ArchiveBrowser", prompts)
        self.assertIn("WorkspaceEditor", prompts)
        self.assertIn("normal file-reading tool", prompts)
        metric_values = {
            event["step_id"]: event["outputs"]["value"]
            for event in self._events(checkpoint.run_id)
            if event.get("event") == "step_completed"
            and event.get("step_id")
            in {"width", "min_coverage", "cohesion_groups"}
        }
        self.assertEqual(
            metric_values,
            {"width": 10, "min_coverage": 0.5, "cohesion_groups": 2},
        )

    def _advance_through_analysis(self) -> RuleWorkflowCheckpoint:
        started = self._start()
        self.assertEqual(
            {step.step_id for step in started.steps},
            {"analyze_protocol", "select_candidates"},
        )
        prompts = [step.prompt for step in started.steps]
        step_ids = [step.step_id for step in started.steps]
        analysis = next(
            step for step in started.steps if step.step_id == "analyze_protocol"
        )
        selection = next(
            step for step in started.steps if step.step_id == "select_candidates"
        )
        candidate_inspections = self.sut.flow_next({
            analysis.instance_id: self._protocol_analysis(),
            selection.instance_id: {
                "dispositions": [
                    {
                        "candidate_id": f"candidate-{index}",
                        "disposition": "INSPECT",
                        "reasoning": "The declaration may conform or provide defaults.",
                        "evidence": "The candidate metadata references DocumentService.",
                    }
                    for index in range(1, 4)
                ]
            },
        })
        self.assertEqual(
            [step.step_id for step in candidate_inspections.steps],
            [
                "candidate_reviews-1.inspect_candidate",
                "candidate_reviews-2.inspect_candidate",
                "candidate_reviews-3.inspect_candidate",
            ],
        )
        prompts.extend(step.prompt for step in candidate_inspections.steps)
        step_ids.extend(step.step_id for step in candidate_inspections.steps)
        validated_selection = next(
            event
            for event in self._events(started.run_id)
            if event.get("event") == "step_completed"
            and event.get("step_id") == "validate_selection"
        )
        selected_candidates = [
            SelectedSourceCandidate.model_validate(candidate)
            for candidate in validated_selection["outputs"]["selected_candidates"]
        ]
        candidate_classifications = self.sut.flow_next({
            step.instance_id: {
                "reasoning": "Inspected the exact selected declaration.",
                "evidence": f"Read {candidate.source.path}.",
            }
            for step, candidate in zip(
                candidate_inspections.steps,
                selected_candidates,
            )
        })

        self.assertEqual(
            [step.step_id for step in candidate_classifications.steps],
            [
                "candidate_reviews-1.classify_candidate",
                "candidate_reviews-2.classify_candidate",
                "candidate_reviews-3.classify_candidate",
            ],
        )
        prompts.extend(step.prompt for step in candidate_classifications.steps)
        step_ids.extend(step.step_id for step in candidate_classifications.steps)
        coverage = self.sut.flow_next({
            step.instance_id: {
                "assessment": self._candidate_assessment(candidate)
            }
            for step, candidate in zip(
                candidate_classifications.steps,
                selected_candidates,
            )
        })

        coverage_steps = [
            step
            for step in coverage.steps
            if step.step_id.endswith("classify_requirement_coverage")
        ]
        self.assertIsNone(
            coverage.error,
            coverage.error,
        )
        self.assertEqual(
            len(coverage_steps),
            3,
            {
                "ready": [
                    step.step_id for step in coverage.steps
                ],
                "skipped": [
                    event
                    for event in self._events(started.run_id)
                    if event.get("event") == "step_skipped"
                ],
            },
        )
        prompts.extend(step.prompt for step in coverage_steps)
        step_ids.extend(step.step_id for step in coverage_steps)
        cohesion_ready = self.sut.flow_next({
            step.instance_id: {
                "coverage_entries": self._coverage_entries(step)
            }
            for step in coverage_steps
        })
        self.assertIsNone(cohesion_ready.error, cohesion_ready.error)
        self.assertEqual(
            [step.step_id for step in cohesion_ready.steps],
            ["analyze_cohesion"],
        )
        prompts.extend(step.prompt for step in cohesion_ready.steps)
        step_ids.extend(step.step_id for step in cohesion_ready.steps)
        cohesion = cohesion_ready.steps[0]
        exception = self.sut.flow_next({
            cohesion.instance_id: {
                "requirement_groups": [
                    {
                        "requirement": requirement,
                        "usage_vector": "1,1" if index < 5 else "0,1",
                        "reasoning": "Derived from the completed conformer assessments.",
                        "evidence": f"Requirement {requirement} classifications.",
                    }
                    for index, requirement in enumerate(self._requirements())
                ]
            },
        })
        self.assertEqual(
            [step.step_id for step in exception.steps],
            ["classify_exception"],
        )
        prompts.extend(step.prompt for step in exception.steps)
        step_ids.extend(step.step_id for step in exception.steps)
        return RuleWorkflowCheckpoint(
            run_id=started.run_id,
            result=exception,
            prompts=prompts,
            step_ids=step_ids,
        )

    def _protocol_analysis(self) -> dict[str, object]:
        return {
            "requirements": [
                {
                    "name": requirement,
                    "evidence": f"DocumentService declares {requirement}.",
                }
                for requirement in self._requirements()
            ],
            "default_implementations": [],
        }

    def _candidate_assessment(
        self,
        candidate: SelectedSourceCandidate,
    ) -> dict[str, object]:
        name = candidate.source.unit
        is_conformer = name in {"ArchiveBrowser", "WorkspaceEditor"}
        implementations = (
            [
                {
                    "requirement": requirement,
                    "classification": (
                        "MEANINGFUL"
                        if name == "WorkspaceEditor" or index < 5
                        else "EMPTY"
                    ),
                    "evidence": f"{name}.{requirement} implementation.",
                }
                for index, requirement in enumerate(self._requirements())
            ]
            if is_conformer
            else []
        )
        return {
            "candidate_id": candidate.candidate_id,
            "location": str(candidate.source.path),
            "classification": "CONFORMER" if is_conformer else "NOT_RELEVANT",
            "name": name,
            "implementations": implementations,
            "default_implementations": [],
            "evidence": f"Inspected {candidate.source.path}.",
        }

    def _coverage_entries(self, step) -> list[dict[str, object]]:
        if (
            "ArchiveBrowser" not in step.prompt
            and "WorkspaceEditor" not in step.prompt
        ):
            return []
        complete = "WorkspaceEditor" in step.prompt
        return [
            {
                "observation_id": requirement,
                "matches": complete or index < 5,
                "included": True,
                "reasoning": "Meaningful or delegated implementations are covered.",
                "evidence": f"Conformer implementation for {requirement}.",
            }
            for index, requirement in enumerate(self._requirements())
        ]

    @staticmethod
    def _requirements() -> list[str]:
        return [
            "open", "list", "search", "metadata", "preview",
            "create", "update", "rename", "move", "delete",
        ]

    def _events(self, run_id: str) -> list[dict[str, object]]:
        path = self.project_root / "runs" / run_id / "events.jsonl"
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
