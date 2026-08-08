"""Verifies the complete DRY-search proof and submission enforcement lifecycle."""

from pathlib import Path

from dry_search_scenario_builder import DrySearchScenarioBuilder
from dry_search_scenario_building import DrySearchScenarioBuilding
from dry_search_scenario_driver import DrySearchScenarioDriver
from dry_search_scenario_driving import DrySearchScenarioDriving


"""
solid-name: TestDrySearchEnforcementIntegration
solid-category: integration-test
solid-description: Verifies health-check submission unlocks only after a valid completed DRY search.
"""
class TestDrySearchEnforcementIntegration:
    def setup_method(self) -> None:
        self.builder: DrySearchScenarioBuilding = DrySearchScenarioBuilder()
        self.driver: DrySearchScenarioDriving = DrySearchScenarioDriver()

    def test_submission_unlocks_after_valid_zero_result_search(self, tmp_path: Path) -> None:
        scenario = self.builder.build(tmp_path)

        outcome = self.driver.run(scenario, tmp_path)

        assert outcome.initial_error == "dry_search_required"
        assert outcome.malformed_search.startswith("Error:")
        assert outcome.blocked_error == "dry_search_required"
        assert outcome.zero_match_search.startswith("No files matched")
        assert outcome.accepted_violations == []
        assert outcome.submission_call_count == 1
