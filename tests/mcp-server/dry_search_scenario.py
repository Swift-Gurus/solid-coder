"""Defines configured collaborators for a DRY-search integration scenario."""

from dataclasses import dataclass
from unittest.mock import MagicMock

from health.dry_search_coordinator import DrySearchCoordinator
from health.dry_search_enforcing_batch_findings_submitter import (
    DrySearchEnforcingBatchFindingsSubmitter,
)


"""
solid-name: DrySearchScenario
solid-category: test-support
solid-description: Holds configured collaborators for one DRY-search enforcement scenario.
"""
@dataclass(frozen=True)
class DrySearchScenario:
    search: DrySearchCoordinator
    submission: DrySearchEnforcingBatchFindingsSubmitter
    submission_backend: MagicMock
