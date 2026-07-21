"""
solid-name: ActiveRunLocator
solid-category: service
solid-spec: [SPEC-013]
solid-description: Resolves the location of the currently active run.
"""

from __future__ import annotations

from harness.active_run_location import ActiveRunLocation
from harness.active_run_pointer_storing import ActiveRunPointerStoring
from harness.runs_base_dir_resolving import RunsBaseDirResolving


class ActiveRunLocator:

    def __init__(
        self,
        base_dir_resolver: RunsBaseDirResolving,
        active_run: ActiveRunPointerStoring,
    ) -> None:
        self._base_dir_resolver = base_dir_resolver
        self._active_run = active_run

    def locate(self) -> ActiveRunLocation:
        base_dir = self._base_dir_resolver.resolve()
        run_id = self._active_run.read(base_dir)
        run_dir = base_dir / run_id
        return ActiveRunLocation(
            run_id=run_id,
            base_dir=base_dir,
            run_dir=run_dir,
            events_path=str(run_dir / "events.jsonl"),
            workflow_path=str(run_dir / "workflow.yaml"),
        )
