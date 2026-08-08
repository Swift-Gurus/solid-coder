"""
solid-name: ActiveRunLockClearer
solid-category: service
solid-spec: [SPEC-031]
solid-description: Clears a stuck run's lock after validating the run identifier matches the currently active run.
"""

from __future__ import annotations

from harness.active_run_lock_clearing import ActiveRunLockClearing
from harness.active_run_locating import ActiveRunLocating
from harness.active_run_pointer_storing import ActiveRunPointerStoring


class ActiveRunLockClearer(ActiveRunLockClearing):

    def __init__(self, run_locator: ActiveRunLocating, active_run: ActiveRunPointerStoring) -> None:
        self._run_locator = run_locator
        self._active_run = active_run

    def clear(self, run_id: str) -> str:
        try:
            location = self._run_locator.locate()
        except FileNotFoundError:
            return "No active run lock exists — nothing to clear."
        if location.run_id != run_id:
            raise ValueError(
                f"run_id mismatch: the currently active run is '{location.run_id}', not '{run_id}'. "
                "Call flow_status first and pass its exact run_id to confirm."
            )
        self._active_run.delete(location.base_dir)
        return (
            f"Cleared the lock for run '{run_id}'. Its event log is preserved at {location.events_path} "
            "for reference. You can now call flow_start."
        )
