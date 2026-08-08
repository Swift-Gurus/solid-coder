"""
solid-name: ActiveRunPointerStore
solid-category: service
solid-spec: [SPEC-031]
solid-description: Stores and retrieves the active run identifier, scoped per session.
"""

from __future__ import annotations

from pathlib import Path

from harness.active_run_exists_error import ActiveRunExistsError
from harness.atomic_file_writing import AtomicFileWriting
from harness.json_loading import JsonLoader, JsonLoading
from harness.posix_atomic_file_writer import POSIXAtomicFileWriter
from harness.session_scoped_active_path_resolver import SessionScopedActivePathResolver
from harness.session_scoped_active_path_resolving import SessionScopedActivePathResolving
from json_serializer import JsonSerializer, JsonSerializing


class ActiveRunPointerStore:

    def __init__(
        self,
        writer: AtomicFileWriting | None = None,
        path_resolver: SessionScopedActivePathResolving | None = None,
        loader: JsonLoading | None = None,
        serializer: JsonSerializing | None = None,
    ) -> None:
        self._writer: AtomicFileWriting = writer or POSIXAtomicFileWriter()
        self._path_resolver: SessionScopedActivePathResolving = path_resolver or SessionScopedActivePathResolver()
        self._loader: JsonLoading = loader or JsonLoader()
        self._serializer: JsonSerializing = serializer or JsonSerializer()

    def read(self, base_dir: Path) -> str:
        active_path = self._path_resolver.resolve(base_dir)
        data = self._loader.safe_load(active_path.read_text())
        return data["run_id"]

    def write(self, base_dir: Path, run_id: str) -> None:
        base_dir.mkdir(parents=True, exist_ok=True)
        active_path = self._path_resolver.resolve(base_dir)
        content = self._serializer.serialize({"run_id": run_id}).encode()
        try:
            self._writer.write_exclusive(active_path, content)
        except FileExistsError:
            existing = self._loader.safe_load(active_path.read_text())
            raise ActiveRunExistsError(existing.get("run_id", "unknown"))

    def delete(self, base_dir: Path) -> None:
        try:
            self._path_resolver.resolve(base_dir).unlink()
        except FileNotFoundError:
            pass
