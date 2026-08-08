"""Prepares a DRY-search integration scenario."""

from pathlib import Path
from unittest.mock import MagicMock

from health.dry_search_service_factory import DrySearchServiceFactory
from dry_search_scenario import DrySearchScenario


"""
solid-name: DrySearchScenarioBuilder
solid-category: test-support
solid-description: Prepares isolated collaborators for a DRY-search enforcement scenario.
"""
class DrySearchScenarioBuilder:
    def build(self, output_dir: Path) -> DrySearchScenario:
        (output_dir / "hook-input.json").write_text("{}\n", encoding="utf-8")
        search_backend = MagicMock()
        search_backend.search.return_value = (
            "No files matched in /project (12 files scanned)."
        )
        submission_backend = MagicMock()
        submission_backend.submit_batch.return_value = {"violations": []}
        factory = DrySearchServiceFactory()
        return DrySearchScenario(
            search=factory.make_search(search_backend),
            submission=factory.make_submission(submission_backend),
            submission_backend=submission_backend,
        )
