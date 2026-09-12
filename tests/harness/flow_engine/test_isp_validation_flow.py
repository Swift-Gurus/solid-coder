"""
solid-name: test_isp_validation_flow
solid-category: integration-test
solid-spec: [SPEC-039]
solid-description: Verifies canonical ISP instructions, protocol applicability, typed observations, exception handling, scoring, and audit behavior.
"""

from __future__ import annotations

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
from source.file_analysis_source import FileAnalysisSource  # noqa: E402
from source.prepare_search_targets_input import PrepareSearchTargetsInput  # noqa: E402
from source.prepare_search_targets_operation_factory import (  # noqa: E402
    PrepareSearchTargetsOperationFactory,
)
from source.search_target_granularity import SearchTargetGranularity  # noqa: E402
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
                output={
                    "analysis": {
                        "requirements": [
                            {
                                "name": "fetch",
                                "evidence": "ISP_SHARED_ANALYSIS_EVIDENCE",
                            }
                        ],
                        "default_implementations": [],
                    }
                },
            ),
            *[
                RuleAnalysisExpectation(
                    step_id="classify_conformer",
                    output={
                        "assessment": {
                            "classification": "NOT_RELEVANT",
                            "name": "Candidate",
                            "implementations": [],
                            "default_implementations": [],
                            "evidence": "ISP_CANDIDATE_EVIDENCE",
                        }
                    },
                )
                for _ in range(3)
            ],
        ],
        metrics=[
            RuleMetricExpectation(
                step_id="width",
                metric_id="ISP-1",
                detection_id="ISP-1",
                detection_name="Protocol Width",
                value=10,
                severity="SEVERE",
            ),
            RuleMetricExpectation(
                step_id="min_coverage",
                metric_id="ISP-2",
                detection_id="ISP-2",
                detection_name="Conformer Coverage",
                value=50,
                severity="SEVERE",
            ),
            RuleMetricExpectation(
                step_id="cohesion_groups",
                metric_id="ISP-3",
                detection_id="ISP-3",
                detection_name="Protocol Cohesion Groups",
                value=2,
                severity="SEVERE",
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

    def test_protocol_analysis_is_reused_without_prompt_reserialization(self) -> None:
        started = self._start()

        self.assertEqual([step.step_id for step in started.steps], ["analyze_protocol"])
        candidate_review = self.sut.flow_next({
            started.steps[0].instance_id: self.SCENARIO.analysis[0].output
        })

        self.assertEqual(
            [step.step_id for step in candidate_review.steps],
            ["classify_conformer", "classify_conformer", "classify_conformer"],
        )
        candidate_prompts = "\n".join(
            step.prompt for step in candidate_review.steps
        )
        self.assertIn("ArchiveBrowser", candidate_prompts)
        self.assertIn("WorkspaceEditor", candidate_prompts)
        self.assertIn("normal file-reading tool", candidate_prompts)
        measured = self.sut.flow_next({
            step.instance_id: expectation.output
            for step, expectation in zip(
                candidate_review.steps,
                self.SCENARIO.analysis[1:],
            )
        })

        self.assertEqual(
            {step.step_id for step in measured.steps},
            {"width", "min_coverage", "cohesion_groups", "classify_exception"},
        )
        self.assertTrue(all(
            "ISP_SHARED_ANALYSIS_EVIDENCE" not in step.prompt
            for step in measured.steps
        ))
        self.assertTrue(all(
            "previously submitted" in step.prompt
            for step in measured.steps
            if step.step_id != "classify_exception"
        ))
        cohesion = next(
            step for step in measured.steps
            if step.step_id == "cohesion_groups"
        )
        self.assertIn("binary implementation vector", cohesion.prompt)
        self.assertIn("identical vectors", cohesion.prompt)
