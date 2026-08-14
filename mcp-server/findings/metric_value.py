"""Defines one immutable review metric measurement."""

from __future__ import annotations

from typing import Union

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from findings.metric_additional_info import MetricAdditionalInfo


MetricScalar = Union[int, float, str]


"""
solid-name: MetricValue
solid-category: model
solid-description: Represents one immutable review metric measurement.
"""
@dataclass(frozen=True, config=ConfigDict(extra="forbid"))
class MetricValue:
    name: str
    value: MetricScalar
    is_exception: bool
    additional_info: MetricAdditionalInfo
