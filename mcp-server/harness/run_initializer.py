"""
solid-name: RunInitializer
solid-category: service
solid-spec: [SPEC-013]
solid-description: Initializes a new run with a unique identifier and directory location.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from harness.active_run_pointer_storing import ActiveRunPointerStoring
from harness.models import FlowDef
from harness.run_directory_scaffolding import RunDirectoryScaffolding
from harness.run_init import RunInit


class RunInitializer:

    def __init__(
        self,
        active_run: ActiveRunPointerStoring,
        scaffolder: RunDirectoryScaffolding,
    ) -> None:
        self._active_run = active_run
        self._scaffolder = scaffolder

    def initialize(self, base_dir: Path, flow_def: FlowDef) -> RunInit:
        run_id = uuid.uuid4().hex
        self._active_run.write(base_dir, run_id)
        run_dir = self._scaffolder.scaffold(base_dir, run_id, flow_def)
        return RunInit(run_id=run_id, run_dir=run_dir)
