"""Defines authored and runtime identity for one expanded co-located metric."""

from __future__ import annotations

from dataclasses import dataclass

"""
solid-name: CoLocatedMetricIdentity
solid-category: model
solid-spec: [SPEC-058]
solid-description: Associates one compact metric ID with its qualified runtime ID and workflow scope.
"""


@dataclass(frozen=True)
class CoLocatedMetricIdentity:
    authored_id: str
    runtime_id: str
    owning_alias: str | None
