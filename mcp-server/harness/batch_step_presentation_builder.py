"""Builds compact batch presentation identity."""

from harness.batch_step_group_identity import BatchStepGroupIdentity
from harness.batch_step_presentation import BatchStepPresentation
from harness.batch_step_presentation_building import BatchStepPresentationBuilding
from harness.combined_rule_batch_step_group_identity import (
    CombinedRuleBatchStepGroupIdentity,
)
from harness.combined_rule_batch_step_presentation import (
    CombinedRuleBatchStepPresentation,
)
from harness.expression_evaluating import ExpressionEvaluating
from harness.flow_validation_error import FlowValidationError
from harness.for_each_declaration import ForEachDeclaration
from harness.models import StepDef
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: BatchStepPresentationBuilder
solid-category: service
solid-spec: [SPEC-042]
solid-description: Builds one batch item's domain label and typed sibling identity from already resolved workflow context.
"""
class BatchStepPresentationBuilder(BatchStepPresentationBuilding):
    def __init__(self, expression_evaluator: ExpressionEvaluating) -> None:
        self._expression_evaluator = expression_evaluator

    def build(
        self,
        step: StepDef,
        declaration: ForEachDeclaration,
        context: WorkflowRunContext,
    ) -> BatchStepPresentation:
        if declaration.label is None:
            raise FlowValidationError(
                f"Step '{step.id}' batch for_each has no label expression"
            )
        label = self._expression_evaluator.evaluate(
            declaration.label.value,
            context,
        )
        if not isinstance(label, str) or not label:
            raise FlowValidationError(
                f"Step '{step.id}' batch for_each label must resolve to a "
                "non-empty string"
            )
        workflow_instance = step.workflow_instance
        if workflow_instance is None:
            group = BatchStepGroupIdentity(None, step.id)
        elif workflow_instance.combined_presentation is not None:
            combined = workflow_instance.combined_presentation
            return CombinedRuleBatchStepPresentation(
                group=CombinedRuleBatchStepGroupIdentity(
                    combined.group_alias
                ),
                label=label,
                rule_alias=combined.rule_alias,
            )
        else:
            group = BatchStepGroupIdentity(
                workflow_instance.alias,
                workflow_instance.steps.require_execution(
                    step.id
                ).local_step_id,
            )
        return BatchStepPresentation(group=group, label=label)
