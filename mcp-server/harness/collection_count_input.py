"""Defines the input for deterministic intermediate collection counting."""

from pydantic import BaseModel, ConfigDict

"""
solid-name: CollectionCountInput
solid-category: model
solid-spec: [SPEC-057]
solid-description: Supplies the complete ordered collection counted by an engine-owned workflow operation.
"""


class CollectionCountInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    values: list[object]
