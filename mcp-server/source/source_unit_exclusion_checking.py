"""Defines exact source-unit exclusion checks."""

from pathlib import Path
from typing import Protocol

from source.repository_source_unit import RepositorySourceUnit
from source.source_unit_identity import SourceUnitIdentity


"""
solid-name: SourceUnitExclusionChecking
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for determining whether a repository unit is the reviewed source unit.
"""
class SourceUnitExclusionChecking(Protocol):
    def is_excluded(
        self,
        project_root: Path,
        unit: RepositorySourceUnit,
        exclusions: list[SourceUnitIdentity],
    ) -> bool: ...
