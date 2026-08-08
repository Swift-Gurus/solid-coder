"""Defines one immutable review metric measurement."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union


MetricScalar = Union[int, float, str]


"""
solid-name: MetricValue
solid-category: model
solid-description: Represents one named metric measurement and its optional contextual details.
"""
@dataclass(frozen=True)
class MetricValue:
    name: str
    value: MetricScalar
    additional_info_json: Optional[str] = None
