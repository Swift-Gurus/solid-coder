"""
solid-name: RunInitializer
solid-category: service
solid-spec: [SPEC-031]
solid-description: Prepares and registers a new run for execution.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Callable

from harness.active_run_pointer_storing import ActiveRunPointerStoring
from harness.models import FlowDef
from harness.run_directory_scaffolding import RunDirectoryScaffolding
from harness.run_init import RunInit


RunIdFactory = Callable[[], str]


"""
solid-name: RunInitializer
solid-category: service
solid-spec: [SPEC-031, SPEC-047]
solid-description: Provisions run directories and registers active pointers only for session-owned runs.
"""
class RunInitializer:

    def __init__(
        self,
        active_run: ActiveRunPointerStoring,
        scaffolder: RunDirectoryScaffolding,
        run_id_factory: RunIdFactory = lambda: uuid.uuid4().hex,
    ) -> None:
        self._active_run = active_run
        self._scaffolder = scaffolder
        self._run_id_factory = run_id_factory

    def initialize(self, base_dir: Path, flow_def: FlowDef, self_contained: bool = False) -> RunInit:
        run_id = self._run_id_factory()
        if self_contained:
            run_dir = self._scaffolder.scaffold(base_dir, run_id, flow_def)
        else:
            self._active_run.write(base_dir, run_id)
            run_dir = self._scaffolder.scaffold(base_dir, run_id, flow_def)
        return RunInit(run_id=run_id, run_dir=run_dir)
