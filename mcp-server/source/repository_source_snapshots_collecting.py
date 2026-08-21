"""Defines repository source snapshot collection."""

from pathlib import Path
from typing import Protocol

from source.repository_source_snapshot import RepositorySourceSnapshot


"""
solid-name: RepositorySourceSnapshotsCollecting
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for collecting stable readable source snapshots beneath one canonical project root.
"""
class RepositorySourceSnapshotsCollecting(Protocol):
    def collect(self, project_root: Path) -> list[RepositorySourceSnapshot]: ...
