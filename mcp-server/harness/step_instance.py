"""Defines one ready execution of a workflow step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from harness.batch_step_presentation import BatchStepPresentation
from harness.collection_metric_calculation import CollectionMetricCalculation
from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.step_outputs import StepOutputs
from harness.step_skip import StepSkip

"""
solid-name: StepInstance
solid-category: model
solid-spec: [SPEC-030, SPEC-037]
solid-description: Represents one ready workflow-step execution within a flow transition.
"""


@dataclass(frozen=True)
class StepInstance:
    step_id: str
    instance_id: str
    item: Any
    prompt: str
    iteration_index: int | None = None
    automatic_outputs: StepOutputs | None = None
    automatic_empty_collection: bool = False
    metric_calculation: CollectionMetricCalculation | None = None
    skip: StepSkip | None = None
    workflow_instance: IncludedWorkflowInstance | None = None
    batch: BatchStepPresentation | None = None
    authored_prompt: str | None = None
    submission_id: str | None = None

    @property
    def is_for_each(self) -> bool:
        return self.iteration_index is not None
