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
from harness.project_context import ProjectDirectory
from harness.review_result import ReviewResult
from harness.rule_review_result import RuleReviewResult
from harness.runs_base_dir_resolver import RunsBaseDirResolver
from harness.static_session_id_reader import StaticSessionIdReader
from review_unit_workflow_parameters import ReviewUnitWorkflowParameters
from review_unit_workflow_context import ReviewUnitWorkflowContext
from review_unit_workflow_target import ReviewUnitWorkflowTarget
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
        self.project_directory = ProjectDirectory(path=self.project_root)
        self.review_unit = self.SCENARIO.fixture_path.read_text(encoding="utf-8")
        self.review_unit_name = f"{self.SCENARIO.workflow_id}-fixture-unit"
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
        checkpoint = self._complete_workflow()

        self.assertEqual(
            set(checkpoint.step_ids),
            {
                *(analysis.step_id for analysis in self.SCENARIO.analysis),
                *(metric.step_id for metric in self.SCENARIO.metrics),
                "classify_exception",
            },
        )
        self.assertNotIn("score_results", checkpoint.step_ids)
        prompts = "\n".join(checkpoint.prompts)
        self.assertNotIn(self.review_unit, prompts)
        self.assertIn(self.review_unit_name, prompts)

    def test_declares_expected_rule_applicability(self) -> None:
        operation_registry = OperationRegistry(
            registrations=SourceOperationRegistrationsFactory(
                project_directory=self.project_directory,
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
        checkpoint = self._complete_workflow()
        rule = self.SCENARIO.rule_path.read_text(encoding="utf-8")
        reader = RuleInstructionBlockReader()

        for metric in self.SCENARIO.metrics:
            definition = reader.definition(
                rule,
                metric.detection_id,
                metric.detection_name,
            )
            detection = reader.detection(
                rule,
                metric.detection_id,
                metric.detection_name,
            )
            if definition is not None:
                self.assertTrue(
                    any(definition in prompt for prompt in checkpoint.prompts),
                    f"Missing {metric.detection_id} definition",
                )
            self.assertTrue(
                any(detection in prompt for prompt in checkpoint.prompts),
                f"Missing {metric.detection_id} instructions",
            )
        if self.SCENARIO.has_authored_exceptions:
            self.assertTrue(
                any(
                    reader.exceptions(rule) in prompt
                    for prompt in checkpoint.prompts
                )
            )
        else:
            self.assertTrue(any(
                "no rule-wide exception" in prompt.lower()
                for prompt in checkpoint.prompts
            ))

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
        checkpoint = self._complete_workflow()
        completed = checkpoint.result

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
        checkpoint = self._complete_workflow(is_exception=True)
        completed = checkpoint.result

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
        parameters = ReviewUnitWorkflowParameters(
            review_unit=ReviewUnitWorkflowContext(
                target=ReviewUnitWorkflowTarget(name=self.review_unit_name)
            )
        )
        return self.sut.flow_start(
            self.SCENARIO.workflow_id,
            parameters.model_dump(),
        )

    def _advance_through_analysis(self) -> RuleWorkflowCheckpoint:
        current = self._start()
        run_id = current.run_id
        prompts = [step.prompt for step in current.steps]
        step_ids = [step.step_id for step in current.steps]
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
            step_ids.extend(ready_step.step_id for ready_step in current.steps)
        return RuleWorkflowCheckpoint(
            run_id=run_id,
            result=current,
            prompts=prompts,
            step_ids=step_ids,
        )

    def _complete_workflow(
        self,
        is_exception: bool = False,
    ) -> RuleWorkflowCheckpoint:
        checkpoint = self._advance_through_analysis()
        current = checkpoint.result
        prompts = list(checkpoint.prompts)
        step_ids = list(checkpoint.step_ids)
        while current.steps:
            current = self.sut.flow_next({
                step.instance_id: self._output_for(
                    step.step_id,
                    is_exception=is_exception,
                )
                for step in current.steps
            })
            prompts.extend(step.prompt for step in current.steps)
            step_ids.extend(step.step_id for step in current.steps)
        self.assertEqual(current.status, "done", current.error)
        return RuleWorkflowCheckpoint(
            run_id=checkpoint.run_id,
            result=current,
            prompts=prompts,
            step_ids=step_ids,
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
