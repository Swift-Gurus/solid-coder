"""Defines immutable metric measurements for one review principle."""

from __future__ import annotations

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from findings.metric_value import MetricValue


"""
solid-name: PrincipleMetrics
solid-category: model
solid-description: Groups immutable metric measurements for one named review principle.
"""
@dataclass(frozen=True, config=ConfigDict(extra="forbid"))
class PrincipleMetrics:
    principle: str
    values: tuple[MetricValue, ...]
