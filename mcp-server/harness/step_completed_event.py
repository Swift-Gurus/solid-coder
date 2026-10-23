"""Defines the typed payload of a persisted step-completion event."""

from __future__ import annotations

from typing import Any

from harness.collection_metric_derivation_projection import (
    CollectionMetricDerivationProjection,
)
from pydantic import BaseModel, ConfigDict, Field

"""
solid-name: StepCompletedEvent
solid-category: model
solid-spec: [SPEC-010, SPEC-030, SPEC-037]
solid-description: Represents persisted step completion state with explicit execution, nested-workflow, local-step, iteration, and source identities.
"""


class StepCompletedEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    step_id: str = ""
    instance_id: str = ""
    outputs: dict[str, Any] = Field(default_factory=dict)
    iteration_index: int | None = None
    workflow_source_index: int | None = None
    workflow_instance_id: str | None = None
    parent_workflow_instance_id: str | None = None
    local_step_id: str | None = None
    item: Any = None
    parent_completed: bool = True
    empty_collection: bool = False
    metric_derivation: CollectionMetricDerivationProjection | None = None
