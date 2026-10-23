"""Defines typed compact metric expansion for resolved workflows."""

from typing import Protocol

from harness.co_located_metric_normalization import CoLocatedMetricNormalization
from harness.include_alias_group import IncludeAliasGroup
from harness.step_declaration import StepDeclaration

"""
solid-name: CoLocatedMetricNormalizing
solid-category: abstraction
solid-spec: [SPEC-058]
solid-description: Contract for expanding co-located measurements while preserving workflow ownership.
"""


class CoLocatedMetricNormalizing(Protocol):
    def normalize(
        self,
        steps: list[StepDeclaration],
        alias_groups: list[IncludeAliasGroup],
        top_level_step_ids: set[str],
    ) -> CoLocatedMetricNormalization: ...
