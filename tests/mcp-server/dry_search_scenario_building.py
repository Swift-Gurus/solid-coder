"""Defines preparation of a DRY-search integration scenario."""

from pathlib import Path
from typing import Protocol

from dry_search_scenario import DrySearchScenario


"""
solid-name: DrySearchScenarioBuilding
solid-category: abstraction
solid-description: Contract for preparing an isolated DRY-search enforcement scenario.
"""
class DrySearchScenarioBuilding(Protocol):
    def build(self, output_dir: Path) -> DrySearchScenario: ...
