"""Defines observable results from a DRY-search integration scenario."""

from dataclasses import dataclass


"""
solid-name: DrySearchScenarioOutcome
solid-category: test-support
solid-description: Captures observable results from one DRY-search enforcement scenario.
"""
@dataclass(frozen=True)
class DrySearchScenarioOutcome:
    initial_error: str
    malformed_search: str
    blocked_error: str
    zero_match_search: str
    accepted_violations: list
    submission_call_count: int
