"""Defines shared deterministic assertions for executable review-rule workflows."""

from __future__ import annotations

import tempfile
import unittest
import sys
from pathlib import Path
from typing import ClassVar

_HARNESS_DIRECTORY = Path(__file__).resolve().parents[1]
if str(_HARNESS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIRECTORY))

from harness.flow_engine_assembly_factory import FlowEngineAssemblyFactory
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.logical_operation_name_validator import LogicalOperationNameValidator
from harness.operation_registry import OperationRegistry
from harness.review_result import ReviewResult
from harness.rule_review_result import RuleReviewResult
from harness.runs_base_dir_resolver import RunsBaseDirResolver
from harness.static_session_id_reader import StaticSessionIdReader
from review_unit_workflow_parameters import ReviewUnitWorkflowParameters
from rule_instruction_block_reader import RuleInstructionBlockReader
from rule_validation_scenario import RuleValidationScenario
from rule_workflow_checkpoint import RuleWorkflowCheckpoint
from source.source_operation_registrations_factory import (
    SourceOperationRegistrationsFactory,
)


"""
solid-name: RuleValidationFlowContract
solid-category: test-support
solid-spec: [SPEC-039]
solid-description: Applies canonical-instruction, response-validation, scoring, exception, and artifact assertions to one executable rule scenario.
"""
class RuleValidationFlowContract(unittest.TestCase):
    __test__ = False

    PROJECT_ROOT: ClassVar[Path]
    SCENARIO: ClassVar[RuleValidationScenario]

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project_root = Path(temporary.name)
        self.review_unit = self.SCENARIO.fixture_path.read_text(encoding="utf-8")
        self.sut = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.project_root
            ),
            plugin_root=self.PROJECT_ROOT,
            session_reader=StaticSessionIdReader(
                f"spec-039-{self.SCENARIO.workflow_id}-test"
            ),
        ).build()

    def test_starts_metrics_and_one_exception_without_scoring_step(self) -> None:
        checkpoint = self._advance_through_analysis()
        started = checkpoint.result

        self.assertEqual(
            {step.step_id for step in started.steps},
            {
                *(metric.step_id for metric in self.SCENARIO.metrics),
                "classify_exception",
            },
        )
        self.assertNotIn("score_results", {step.step_id for step in started.steps})
        self.assertIn(self.review_unit, "\n".join(checkpoint.prompts))

    def test_declares_expected_rule_applicability(self) -> None:
        operation_registry = OperationRegistry(
            registrations=SourceOperationRegistrationsFactory(
                project_directory=lambda: self.project_root,
            ).make(),
            name_validator=LogicalOperationNameValidator(),
            error_factory=FlowValidationErrorFactory(),
        )
        workflow = FlowEngineAssemblyFactory().build(
            operation_registry=operation_registry,
        ).flow_loader.load(
            self.PROJECT_ROOT
            / "workflows"
            / "review"
            / "rules"
            / self.SCENARIO.workflow_id
            / "workflow.yaml",
            [],
        )

        self.assertIsNotNone(workflow.rule)
        self.assertEqual(workflow.rule.scope, self.SCENARIO.rule_scope)
        self.assertEqual(
            workflow.rule.match.file_extensions.included,
            self.SCENARIO.included_file_extensions,
        )
        self.assertEqual(
            workflow.rule.match.unit_kinds.included,
            self.SCENARIO.included_unit_kinds,
        )
        self.assertEqual(
            workflow.rule.match.tags.included,
            self.SCENARIO.included_tags,
        )

    def test_uses_canonical_rule_detection_and_exception_instructions(self) -> None:
        checkpoint = self._advance_through_analysis()
        started = checkpoint.result
        rule = self.SCENARIO.rule_path.read_text(encoding="utf-8")
        reader = RuleInstructionBlockReader()

        for metric in self.SCENARIO.metrics:
            detection = reader.detection(
                rule,
                metric.detection_id,
                metric.detection_name,
            )
            self.assertTrue(
                any(detection in prompt for prompt in checkpoint.prompts),
                f"Missing {metric.detection_id} instructions",
            )
        exception_prompt = next(
            step.prompt
            for step in started.steps
            if step.step_id == "classify_exception"
        )
        if self.SCENARIO.has_authored_exceptions:
            self.assertIn(reader.exceptions(rule), exception_prompt)
        else:
            self.assertIn("no rule-wide exception", exception_prompt.lower())

    def test_rejects_unaudited_measurement_before_scoring(self) -> None:
        started = self._advance_through_analysis().result
        first_metric = self.SCENARIO.metrics[0]
        metric_step = next(
            step
            for step in started.steps
            if step.step_id == first_metric.step_id
        )

        rejected = self.sut.flow_next(
            {metric_step.instance_id: {"value": first_metric.value}}
        )

        self.assertEqual(rejected.status, "ready")
        rejected_metric = next(
            step
            for step in rejected.steps
            if step.step_id == first_metric.step_id
        )
        self.assertIn("additional_info", rejected_metric.rejection_reason)

    def test_mcp_scores_all_metrics_and_publishes_audited_result(self) -> None:
        checkpoint = self._advance_through_analysis()
        started = checkpoint.result

        completed = self.sut.flow_next(
            {
                step.instance_id: self._output_for(step.step_id)
                for step in started.steps
            }
        )

        self.assertEqual(completed.status, "done")
        result = self._rule_result(checkpoint.run_id)
        aggregate = self._aggregate_result(checkpoint.run_id)
        self.assertEqual(result.workflow_id, self.SCENARIO.workflow_id)
        self.assertEqual(result.rule_instance_id, checkpoint.run_id)
        self.assertEqual(result.severity, self.SCENARIO.final_severity)
        self.assertEqual(result.scoring_authority, "mcp")
        self.assertFalse(result.exception.is_exception)
        self.assertEqual(aggregate.rule_results, [result])
        self.assertEqual(
            [metric.metric_id for metric in result.metrics],
            [metric.metric_id for metric in self.SCENARIO.metrics],
        )
        self.assertEqual(
            [metric.observation_id for metric in result.metrics],
            [metric.observation_id for metric in self.SCENARIO.metrics],
        )
        self.assertEqual(
            [metric.value for metric in result.metrics],
            [metric.value for metric in self.SCENARIO.metrics],
        )
        self.assertEqual(
            [metric.severity for metric in result.metrics],
            [metric.severity for metric in self.SCENARIO.metrics],
        )

    def test_exception_makes_metric_decisions_compliant_without_hiding_evidence(self) -> None:
        checkpoint = self._advance_through_analysis()
        started = checkpoint.result

        completed = self.sut.flow_next(
            {
                step.instance_id: self._output_for(
                    step.step_id,
                    is_exception=True,
                )
                for step in started.steps
            }
        )

        self.assertEqual(completed.status, "done")
        result = self._rule_result(checkpoint.run_id)
        self.assertTrue(result.exception.is_exception)
        self.assertEqual(result.severity, "COMPLIANT")
        self.assertEqual(
            [metric.severity for metric in result.metrics],
            ["COMPLIANT" for _ in self.SCENARIO.metrics],
        )
        self.assertTrue(
            all(metric.additional_info.evidence for metric in result.metrics)
        )

    def _start(self):
        parameters = ReviewUnitWorkflowParameters(review_unit=self.review_unit)
        return self.sut.flow_start(
            self.SCENARIO.workflow_id,
            parameters.model_dump(),
        )

    def _advance_through_analysis(self) -> RuleWorkflowCheckpoint:
        current = self._start()
        run_id = current.run_id
        prompts = [step.prompt for step in current.steps]
        for expectation in self.SCENARIO.analysis:
            step = next(
                ready_step
                for ready_step in current.steps
                if ready_step.step_id == expectation.step_id
            )
            current = self.sut.flow_next({
                step.instance_id: expectation.output,
            })
            prompts.extend(ready_step.prompt for ready_step in current.steps)
        return RuleWorkflowCheckpoint(
            run_id=run_id,
            result=current,
            prompts=prompts,
        )

    def _output_for(
        self,
        step_id: str,
        is_exception: bool = False,
    ) -> dict[str, object]:
        additional_info = {
            "reasoning": f"Measured {step_id} from the supplied source.",
            "evidence": f"Canonical {self.SCENARIO.workflow_id} fixture evidence.",
        }
        if step_id == "classify_exception":
            return {
                "is_exception": is_exception,
                "additional_info": additional_info,
            }
        metric = next(
            expectation
            for expectation in self.SCENARIO.metrics
            if expectation.step_id == step_id
        )
        return {
            "value": metric.value,
            "additional_info": additional_info,
        }

    def _rule_result(self, run_id: str) -> RuleReviewResult:
        review_directory = self.project_root / "runs" / run_id / "results" / "review"
        return RuleReviewResult.model_validate_json(
            (
                review_directory
                / self.SCENARIO.workflow_id
                / run_id
                / "result.json"
            ).read_text()
        )

    def _aggregate_result(self, run_id: str) -> ReviewResult:
        review_directory = self.project_root / "runs" / run_id / "results" / "review"
        return ReviewResult.model_validate_json(
            (review_directory / "result.json").read_text()
        )
