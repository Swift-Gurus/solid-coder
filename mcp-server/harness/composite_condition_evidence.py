"""Defines audit evidence for one composed workflow condition."""

from __future__ import annotations

from typing import Literal, Union

from pydantic import BaseModel, ConfigDict

from harness.comparison_condition_evidence import ComparisonConditionEvidence


"""
solid-name: CompositeConditionEvidence
solid-category: model
solid-spec: [SPEC-037]
solid-description: Captures the evaluated child evidence and outcome of one composed workflow condition.
"""
class CompositeConditionEvidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: Literal["all", "any", "not"]
    children: list[
        Union[ComparisonConditionEvidence, "CompositeConditionEvidence"]
    ]
    matched: bool


CompositeConditionEvidence.model_rebuild()
