"""Locates persisted flow runs."""

from __future__ import annotations

from harness.active_run_location import ActiveRunLocation
from harness.active_run_pointer_storing import ActiveRunPointerStoring
from harness.isolated_run_paths import ISOLATED_RUNS_DIRNAME
from harness.runs_base_dir_resolving import RunsBaseDirResolving


"""
solid-name: ActiveRunLocator
solid-category: service
solid-spec: [SPEC-031]
solid-description: Resolves locations for the current session's active run and explicitly identified isolated runs.
"""
class ActiveRunLocator:

    def __init__(
        self,
        base_dir_resolver: RunsBaseDirResolving,
        active_run: ActiveRunPointerStoring,
    ) -> None:
        self._base_dir_resolver = base_dir_resolver
        self._active_run = active_run

    def locate(self, run_id: str | None = None) -> ActiveRunLocation:
        if run_id is None:
            base_dir = self._base_dir_resolver.resolve()
            resolved_run_id = self._active_run.read(base_dir)
            run_dir = base_dir / resolved_run_id
        else:
            base_dir = self._base_dir_resolver.resolve() / ISOLATED_RUNS_DIRNAME / run_id
            try:
                resolved_run_id = self._active_run.read(base_dir)
            except FileNotFoundError:
                raise FileNotFoundError(f"No isolated run found for run_id={run_id}") from None
            if resolved_run_id != run_id:
                raise FileNotFoundError(f"No isolated run found for run_id={run_id}")
            run_dir = base_dir
        return ActiveRunLocation(
            run_id=resolved_run_id,
            base_dir=base_dir,
            run_dir=run_dir,
            events_path=str(run_dir / "events.jsonl"),
            workflow_path=str(run_dir / "workflow.yaml"),
        )
