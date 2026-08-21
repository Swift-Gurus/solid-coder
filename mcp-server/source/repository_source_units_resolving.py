"""Defines searchable-unit resolution for one repository source snapshot."""

from typing import Protocol

from source.repository_source_snapshot import RepositorySourceSnapshot
from source.repository_source_unit import RepositorySourceUnit


"""
solid-name: RepositorySourceUnitsResolving
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for resolving searchable repository-source units from one immutable snapshot.
"""
class RepositorySourceUnitsResolving(Protocol):
    def resolve(
        self,
        snapshot: RepositorySourceSnapshot,
    ) -> list[RepositorySourceUnit]: ...
