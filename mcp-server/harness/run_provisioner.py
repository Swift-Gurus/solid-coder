"""
solid-name: RunProvisioner
solid-category: service
solid-spec: [SPEC-031]
solid-description: Provisions a new run with its identity, directory, and startup metadata.
"""

from __future__ import annotations

from pathlib import Path

from harness.flow_submission_format import FlowSubmissionFormat
from harness.models import FlowDef
from harness.run_init import RunInit
from harness.run_initializing import RunInitializing
from harness.run_metadata import RunMetadata
from harness.run_metadata_persisting import RunMetadataPersisting


class RunProvisioner:
    def __init__(
        self,
        run_initializer: RunInitializing,
        metadata_store: RunMetadataPersisting,
        submission_format: FlowSubmissionFormat = FlowSubmissionFormat.NESTED,
    ) -> None:
        self._run_initializer = run_initializer
        self._metadata_store = metadata_store
        self._submission_format = submission_format

    def provision(
        self,
        base_dir: Path,
        flow_def: FlowDef,
        params: dict,
        self_contained: bool = False,
    ) -> RunInit:
        run_init = self._run_initializer.initialize(
            base_dir, flow_def, self_contained=self_contained
        )
        metadata = RunMetadata(params=params, submission_format=self._submission_format)
        self._metadata_store.write(run_init.run_dir, metadata)
        return run_init
