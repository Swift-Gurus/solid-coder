"""Qualifies collection metric sources within included workflows."""

from harness.collection_source_reference_parsing import (
    CollectionSourceReferenceParsing,
)
from harness.metric_scoring_source_qualifying import (
    MetricScoringSourceQualifying,
)
from harness.step_output_reference import StepOutputReference
from harness.workflow_expression import WorkflowExpression
from harness.workflow_expression_parsing import WorkflowExpressionParsing
from harness.workflow_expression_serializing import WorkflowExpressionSerializing


"""
solid-name: MetricScoringSourceQualifier
solid-category: boundary
solid-spec: [SPEC-053, SPEC-056]
solid-description: Qualifies authored collection metric sources during include expansion.
"""
class MetricScoringSourceQualifier(MetricScoringSourceQualifying):
    def __init__(
        self,
        expression_parser: WorkflowExpressionParsing,
        reference_parser: CollectionSourceReferenceParsing,
        expression_serializer: WorkflowExpressionSerializing,
    ) -> None:
        self._expression_parser = expression_parser
        self._reference_parser = reference_parser
        self._expression_serializer = expression_serializer

    def qualify(
        self,
        scoring: dict,
        alias: str,
        local_step_ids: set[str],
    ) -> dict:
        qualified = dict(scoring)
        source = scoring.get("source")
        if source is None:
            return qualified
        reference = self._reference_parser.parse(
            self._expression_parser.parse(source).value
        )
        if not isinstance(reference, StepOutputReference):
            return qualified
        if reference.step_id not in local_step_ids:
            return qualified
        qualified_reference = StepOutputReference(
            step_id=f"{alias}.{reference.step_id}",
            output_name=reference.output_name,
        )
        qualified["source"] = self._expression_serializer.serialize(
            WorkflowExpression(
                value=(
                    f"steps.{qualified_reference.step_id}.outputs."
                    f"{qualified_reference.output_name}"
                )
            )
        )
        return qualified
