"""Defines discovery of configured metric rule identifiers."""

from pathlib import Path
from typing import Protocol

from scoring.metric_id_catalog import MetricIdCatalog


"""
solid-name: MetricIdDiscovering
solid-category: abstraction
solid-description: Contract for discovering configured metric rule identifiers from a principle rule source.
"""
class MetricIdDiscovering(Protocol):
    def discover(self, rule_path: Path) -> MetricIdCatalog: ...
