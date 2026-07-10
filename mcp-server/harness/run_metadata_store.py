"""
solid-name: RunMetadataStore
solid-category: service
solid-spec: [SPEC-013]
solid-description: Provides persistent storage and retrieval of run metadata.
"""

from __future__ import annotations

import json
from pathlib import Path

from harness.run_metadata import RunMetadata
from harness.run_metadata_persisting import RunMetadataPersisting


class RunMetadataStore:

    def write(self, run_dir: Path, metadata: RunMetadata) -> None:
        (run_dir / "run-metadata.json").write_text(
            json.dumps({"params": metadata.params, "detected_env": metadata.detected_env})
        )

    def read(self, run_dir: Path) -> RunMetadata:
        data = json.loads((run_dir / "run-metadata.json").read_text())
        return RunMetadata(params=data["params"], detected_env=data["detected_env"])