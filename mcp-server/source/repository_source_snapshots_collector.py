"""Collects immutable readable source snapshots beneath a project root."""

from pathlib import Path

from harness.content_hashing import ContentHashing
from source.repository_source_files_discovering import (
    RepositorySourceFilesDiscovering,
)
from source.repository_source_snapshot import RepositorySourceSnapshot
from source.repository_source_snapshots_collecting import (
    RepositorySourceSnapshotsCollecting,
)


"""
solid-name: RepositorySourceSnapshotsCollector
solid-category: service
solid-spec: [SPEC-040]
solid-description: Collects stable, ordered snapshots of readable source files for repository analysis and search.
"""
class RepositorySourceSnapshotsCollector(RepositorySourceSnapshotsCollecting):
    def __init__(
        self,
        files: RepositorySourceFilesDiscovering,
        content_hasher: ContentHashing,
    ) -> None:
        self._files = files
        self._content_hasher = content_hasher

    def collect(self, project_root: Path) -> list[RepositorySourceSnapshot]:
        root = project_root.resolve()
        snapshots: list[RepositorySourceSnapshot] = []
        for path in self._files.discover(root):
            resolved_path = path.resolve()
            try:
                source_identity = resolved_path.relative_to(root).as_posix()
            except ValueError:
                continue
            try:
                content_bytes = resolved_path.read_bytes()
            except OSError:
                continue
            if b"\x00" in content_bytes[:1024]:
                continue
            snapshots.append(RepositorySourceSnapshot(
                path=resolved_path,
                source_identity=source_identity,
                content=content_bytes.decode("utf-8", errors="replace"),
                content_sha256=self._content_hasher.hash(content_bytes),
            ))
        return sorted(snapshots, key=lambda snapshot: snapshot.source_identity)
