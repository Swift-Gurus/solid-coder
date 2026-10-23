"""Defines ratio reducer input."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, StrictFloat, StrictInt

"""
solid-name: RatioMetricReducerDeclaration
solid-category: model
solid-spec: [SPEC-054, SPEC-059]
solid-description: Defines numerator and denominator conditions for deterministic ratio metrics.
"""


class RatioMetricReducerDeclaration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    type: Literal["ratio"]
    numerator_when: object
    denominator_when: object
    empty_value: StrictInt | StrictFloat | None = None
