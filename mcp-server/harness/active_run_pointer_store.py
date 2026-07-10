"""
solid-name: ActiveRunPointerStore
solid-category: service
solid-spec: [SPEC-013]
solid-description: Manages exclusive read, write, and delete operations for the active run identifier.
"""

from __future__ import annotations

import json
from pathlib import Path

from harness.active_run_exists_error import ActiveRunExistsError
from harness.atomic_file_writing import AtomicFileWriting
from harness.posix_atomic_file_writer import POSIXAtomicFileWriter


class ActiveRunPointerStore:

    def __init__(self, writer: AtomicFileWriting | None = None) -> None:
        self._writer: AtomicFileWriting = writer or POSIXAtomicFileWriter()

    def read(self, base_dir: Path) -> str:
        data = json.loads((base_dir / "active.json").read_text())
        return data["run_id"]

    def write(self, base_dir: Path, run_id: str) -> None:
        base_dir.mkdir(parents=True, exist_ok=True)
        active_path = base_dir / "active.json"
        content = json.dumps({"run_id": run_id}).encode()
        try:
            self._writer.write_exclusive(active_path, content)
        except FileExistsError:
            existing = json.loads(active_path.read_text())
            raise ActiveRunExistsError(existing.get("run_id", "unknown"))

    def delete(self, base_dir: Path) -> None:
        try:
            (base_dir / "active.json").unlink()
        except FileNotFoundError:
            pass
