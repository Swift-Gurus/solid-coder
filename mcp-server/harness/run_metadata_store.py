"""
solid-name: RunMetadataStore
solid-category: service
solid-spec: [SPEC-031]
solid-description: Provides persistent storage and retrieval of run metadata.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from harness.run_metadata import RunMetadata
from harness.run_metadata_persisting import RunMetadataPersisting
from pydantic import TypeAdapter


class RunMetadataStore(RunMetadataPersisting):
    def write(self, run_dir: Path, metadata: RunMetadata) -> None:
        (run_dir / "run-metadata.json").write_text(json.dumps(asdict(metadata)))

    def read(self, run_dir: Path) -> RunMetadata:
        return TypeAdapter(RunMetadata).validate_json(
            (run_dir / "run-metadata.json").read_text()
        )
