"""Defines the compact persisted projection of a collection metric derivation."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from harness.step_output_reference import StepOutputReference


"""
solid-name: CollectionMetricDerivationProjection
solid-category: model
solid-spec: [SPEC-053]
solid-description: Locates the durable evidence supporting one derived metric without copying its source payload.
"""
class CollectionMetricDerivationProjection(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    kind: Literal["collection_count"] = "collection_count"
    source: StepOutputReference
    source_size: int = Field(ge=0)
    matched_indexes: list[int]
    excluded_indexes: list[int]
