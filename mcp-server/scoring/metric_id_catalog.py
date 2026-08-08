"""Defines the immutable rule identifiers available to a principle scorer."""

from __future__ import annotations

from dataclasses import dataclass


"""
solid-name: MetricIdCatalog
solid-category: model
solid-description: Provides immutable access to the rule identifiers configured for one review principle.
"""
@dataclass(frozen=True)
class MetricIdCatalog:
    identifiers: tuple[str, ...]
