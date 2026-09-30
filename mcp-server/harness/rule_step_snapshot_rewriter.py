"""Rewrites typed rule steps into their public workflow YAML fields."""

from harness.condition_serializing import ConditionSerializing
from harness.step_def import StepDef
from harness.pairwise_relation_declaration import PairwiseRelationDeclaration
from harness.step_snapshot_rewriting import StepSnapshotRewriting
from harness.workflow_expression_serializing import WorkflowExpressionSerializing


"""
solid-name: RuleStepSnapshotRewriter
solid-category: boundary
solid-spec: [SPEC-039, SPEC-054, SPEC-056]
solid-description: Normalizes rule-step snapshots for their public workflow representation.
"""
class RuleStepSnapshotRewriter(StepSnapshotRewriting):
    def __init__(
        self,
        condition_serializer: ConditionSerializing,
        expression_serializer: WorkflowExpressionSerializing,
    ) -> None:
        self._condition_serializer = condition_serializer
        self._expression_serializer = expression_serializer

    def rewrite(self, snapshot: dict, step: StepDef) -> None:
        snapshot.pop("metric", None)
        snapshot.pop("metric_calculation", None)
        if step.assessment is not None:
            snapshot.pop("outputs", None)
            snapshot["assessment"] = step.assessment.model_dump(
                mode="json",
                exclude_none=True,
                by_alias=True,
            )
            return
        if step.type not in {"metric", "exception"}:
            return
        snapshot.pop("outputs", None)
        if step.metric is None:
            return
        snapshot["metric_id"] = step.metric.metric_id
        if step.metric.observation_id != "value":
            snapshot["observation_id"] = step.metric.observation_id
        snapshot["value"] = step.metric.value.model_dump(
            mode="json",
            exclude_none=True,
        )
        scoring = step.metric.scoring.model_dump(
            mode="json",
            exclude_none=True,
        )
        calculation = step.metric_calculation
        if calculation is not None:
            scoring["source"] = self._expression_serializer.serialize(
                calculation.source.expression
            )
            if calculation.condition is not None:
                scoring["when"] = self._condition_serializer.serialize(
                    calculation.condition
                )
            reducer = calculation.reducer
            if reducer is not None:
                serialized_reducer = {"type": reducer.type.value}
                if reducer.relation is not None:
                    serialized_reducer["relation"] = PairwiseRelationDeclaration(
                        operator=reducer.relation.operator,
                        left=self._expression_serializer.serialize(reducer.relation.left),
                        right=self._expression_serializer.serialize(reducer.relation.right),
                    ).model_dump(mode="json")
                if reducer.value is not None:
                    serialized_reducer["value"] = (
                        self._expression_serializer.serialize(reducer.value)
                    )
                if reducer.empty_value is not None:
                    serialized_reducer["empty_value"] = reducer.empty_value
                if reducer.numerator_condition is not None:
                    serialized_reducer["numerator_when"] = (
                        self._condition_serializer.serialize(
                            reducer.numerator_condition
                        )
                    )
                if reducer.denominator_condition is not None:
                    serialized_reducer["denominator_when"] = (
                        self._condition_serializer.serialize(
                            reducer.denominator_condition
                        )
                    )
                scoring["reducer"] = serialized_reducer
        snapshot["scoring"] = scoring
