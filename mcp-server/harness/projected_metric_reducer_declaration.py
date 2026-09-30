"""Defines scalar projection reducer input."""

from typing import Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, StrictFloat, StrictInt, model_validator


"""
solid-name: ProjectedMetricReducerDeclaration
solid-category: model
solid-spec: [SPEC-054, SPEC-059]
solid-description: Defines the supported scalar projection reducers and their empty-collection values.
"""
class ProjectedMetricReducerDeclaration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    type: Literal["maximum", "minimum", "distinct_count"]
    value: object
    empty_value: Optional[Union[StrictInt, StrictFloat]] = None

    @model_validator(mode="after")
    def validate_empty_value(self):
        if self.type == "distinct_count" and "empty_value" in self.model_fields_set:
            raise ValueError("distinct_count reducer has unsupported fields: empty_value")
        return self
