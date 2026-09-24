"""Materializes engine-owned collection metric step instances."""

from __future__ import annotations

from harness.collection_metric_evaluating import CollectionMetricEvaluating
from harness.for_each_items_resolving import ForEachItemsResolving
from harness.models import StepDef, StepInstance, StepOutputs
from harness.step_output_reference import StepOutputReference
from harness.step_instance_building import StepInstanceBuilding
from harness.workflow_run_context import WorkflowRunContext
from harness.workflow_step_context_resolving import WorkflowStepContextResolving


"""
solid-name: CollectionMetricStepInstanceBuilder
solid-category: decorator
solid-spec: [SPEC-053, SPEC-054, SPEC-056]
solid-description: Completes collection-backed metric instances with deterministic engine outputs.
"""
class CollectionMetricStepInstanceBuilder(StepInstanceBuilding):
    def __init__(
        self,
        delegate: StepInstanceBuilding,
        items_resolver: ForEachItemsResolving,
        evaluator: CollectionMetricEvaluating,
        context_resolver: WorkflowStepContextResolving,
    ) -> None:
        self._delegate = delegate
        self._items_resolver = items_resolver
        self._evaluator = evaluator
        self._context_resolver = context_resolver

    def build(
        self,
        step: StepDef,
        context: WorkflowRunContext,
        item: object,
        instance_id: str,
        iteration_index: int | None = None,
    ) -> StepInstance:
        calculation = step.metric_calculation
        if calculation is None:
            return self._delegate.build(
                step,
                context,
                item,
                instance_id,
                iteration_index,
            )
        scoped_context = self._context_resolver.resolve(
            context,
            step.workflow_instance,
            item,
        )
        entries = self._items_resolver.resolve(
            step.id,
            calculation.source,
            scoped_context,
        )
        evaluation = self._evaluator.evaluate(
            calculation,
            entries,
            scoped_context,
        )
        return StepInstance(
            step_id=step.id,
            instance_id=instance_id,
            item=item,
            prompt="",
            iteration_index=iteration_index,
            automatic_outputs=StepOutputs(
                values={
                    "value": evaluation.value,
                    "additional_info": {
                        "reasoning": self._reasoning(evaluation),
                        "evidence": self._evidence(evaluation),
                    },
                }
            ),
            metric_calculation=evaluation,
            workflow_instance=step.workflow_instance,
            authored_prompt="",
        )

    def _reasoning(self, calculation) -> str:
        reducer = calculation.reducer
        if reducer is None:
            return (
                f"Counted {calculation.value} of "
                f"{calculation.source_size} source entries matching "
                "the authored condition."
            )
        return (
            f"Applied the {reducer.type.value} reducer to "
            f"{len(calculation.matched_indexes)} of "
            f"{calculation.source_size} source entries and derived "
            f"{calculation.value}."
        )

    def _evidence(self, calculation) -> str:
        source = calculation.source
        source_reference = (
            f"steps.{source.step_id}.outputs.{source.output_name}"
            if isinstance(source, StepOutputReference)
            else (
                f"workflows.{source.workflow_alias}.outputs."
                f"{source.output_name}"
            )
        )
        projections = ", ".join(
            f"{evidence.index}={evidence.value!r}"
            for evidence in calculation.projection_evidence
        )
        return (
            f"Source {source_reference}; "
            f"matched indexes {calculation.matched_indexes}; excluded indexes "
            f"{calculation.excluded_indexes}; projections [{projections}]; "
            f"distinct indexes {calculation.distinct_indexes}; numerator "
            f"indexes {calculation.numerator_indexes}; denominator indexes "
            f"{calculation.denominator_indexes}; zero denominator "
            f"{calculation.zero_denominator}."
        )
