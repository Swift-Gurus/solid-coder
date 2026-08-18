"""Defines the validated scalar schema authored by one metric step."""

from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, StrictFloat, StrictInt, model_validator

from harness.metric_value_type import MetricValueType


MetricNumericBoundary = Union[StrictInt, StrictFloat]


"""
solid-name: MetricValueDeclaration
solid-category: model
solid-spec: [SPEC-039]
solid-description: Represents the closed scalar JSON schema accepted for one metric observation value.
"""
class MetricValueDeclaration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    type: MetricValueType
    minimum: Optional[MetricNumericBoundary] = None
    maximum: Optional[MetricNumericBoundary] = None

    @model_validator(mode="after")
    def validate_numeric_boundaries(self) -> "MetricValueDeclaration":
        has_boundary = self.minimum is not None or self.maximum is not None
        is_numeric = self.type in {
            MetricValueType.INTEGER,
            MetricValueType.NUMBER,
        }
        if has_boundary and not is_numeric:
            raise ValueError("minimum and maximum are supported only for numeric metric values")
        if (
            self.minimum is not None
            and self.maximum is not None
            and self.minimum > self.maximum
        ):
            raise ValueError("minimum must be less than or equal to maximum")
        return self
