"""Defines inspection of health-check DRY-search completion."""

from typing import Protocol

from health.dry_search_completion_status import DrySearchCompletionStatus


"""
solid-name: DrySearchCompletionChecking
solid-category: abstraction
solid-description: Contract for checking whether a health-check output directory contains valid DRY-search proof.
"""
class DrySearchCompletionChecking(Protocol):
    def status(self, output_dir: str) -> DrySearchCompletionStatus: ...
