"""Defines the typed metric contract attached to a workflow step."""

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator
from typing_extensions import Annotated

from harness.metric_scoring_declaration import MetricScoringDeclaration
from harness.metric_value_declaration import MetricValueDeclaration
from harness.metric_value_type import MetricValueType
from harness.scoring_comparison_operator import ScoringComparisonOperator


MetricId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


"""
solid-name: MetricDeclaration
solid-category: model
solid-spec: [SPEC-039]
solid-description: Associates one stable metric identity with its scalar value and deterministic scoring contracts.
"""
class MetricDeclaration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    metric_id: MetricId
    value: MetricValueDeclaration
    scoring: MetricScoringDeclaration

    @model_validator(mode="after")
    def validate_comparison_types(self) -> "MetricDeclaration":
        bands = [self.scoring.minor, self.scoring.severe]
        for band in (candidate for candidate in bands if candidate is not None):
            if self.value.type in {MetricValueType.STRING, MetricValueType.BOOLEAN}:
                if band.operator not in {
                    ScoringComparisonOperator.EQUALS,
                    ScoringComparisonOperator.NOT_EQUALS,
                }:
                    raise ValueError(
                        "string and boolean metrics support only equals or not_equals"
                    )
            if self.value.type == MetricValueType.BOOLEAN and not isinstance(
                band.value,
                bool,
            ):
                raise ValueError("boolean metric comparisons require a boolean value")
            if self.value.type == MetricValueType.STRING and not isinstance(
                band.value,
                str,
            ):
                raise ValueError("string metric comparisons require a string value")
            if self.value.type == MetricValueType.INTEGER and (
                isinstance(band.value, bool) or not isinstance(band.value, int)
            ):
                raise ValueError("integer metric comparisons require an integer value")
            if self.value.type == MetricValueType.NUMBER and (
                isinstance(band.value, bool)
                or not isinstance(band.value, (int, float))
            ):
                raise ValueError("number metric comparisons require a numeric value")
        return self
