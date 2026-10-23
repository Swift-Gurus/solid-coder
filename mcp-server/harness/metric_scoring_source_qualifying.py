"""Defines include-time qualification of metric scoring sources."""

from typing import Protocol

"""
solid-name: MetricScoringSourceQualifying
solid-category: abstraction
solid-spec: [SPEC-053]
solid-description: Contract for qualifying collection metric sources within included workflows.
"""


class MetricScoringSourceQualifying(Protocol):
    def qualify(
        self,
        scoring: dict,
        alias: str,
        local_step_ids: set[str],
    ) -> dict: ...
