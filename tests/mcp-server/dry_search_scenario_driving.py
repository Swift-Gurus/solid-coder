"""Defines execution of a DRY-search integration scenario."""

from pathlib import Path
from typing import Protocol

from dry_search_scenario import DrySearchScenario
from dry_search_scenario_outcome import DrySearchScenarioOutcome


"""
solid-name: DrySearchScenarioDriving
solid-category: abstraction
solid-description: Contract for executing a DRY-search enforcement scenario.
"""
class DrySearchScenarioDriving(Protocol):
    def run(
        self,
        scenario: DrySearchScenario,
        output_dir: Path,
    ) -> DrySearchScenarioOutcome: ...
