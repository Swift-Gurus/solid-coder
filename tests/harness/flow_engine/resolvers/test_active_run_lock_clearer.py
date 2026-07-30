"""
solid-name: test_active_run_lock_clearer
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Tests clearing a stuck run's lock after confirming the caller named the exact run holding it.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.active_run_location import ActiveRunLocation
from harness.active_run_lock_clearer import ActiveRunLockClearer


class StubRunLocator:
    def __init__(self, location: ActiveRunLocation | None = None) -> None:
        self._location = location

    def locate(self, run_id=None) -> ActiveRunLocation:
        if self._location is None:
            raise FileNotFoundError("no active run")
        return self._location


class SpyActiveRunPointerStore:
    def __init__(self) -> None:
        self.deleted: list[Path] = []

    def read(self, base_dir: Path) -> str:
        raise NotImplementedError

    def write(self, base_dir: Path, run_id: str) -> None:
        raise NotImplementedError

    def delete(self, base_dir: Path) -> None:
        self.deleted.append(base_dir)


def _location(run_id: str = "run-1") -> ActiveRunLocation:
    return ActiveRunLocation(
        run_id=run_id, base_dir=Path("/runs"), run_dir=Path(f"/runs/{run_id}"),
        events_path=f"/runs/{run_id}/events.jsonl", workflow_path=f"/runs/{run_id}/workflow.yaml",
    )


class TestActiveRunLockClearer(unittest.TestCase):

    def test_returns_a_message_when_there_is_no_active_run(self):
        active_run = SpyActiveRunPointerStore()
        sut = ActiveRunLockClearer(run_locator=StubRunLocator(None), active_run=active_run)

        result = sut.clear("run-1")

        self.assertEqual(result, "No active run lock exists — nothing to clear.")
        self.assertEqual(active_run.deleted, [])

    def test_raises_with_the_actual_run_id_when_it_does_not_match(self):
        active_run = SpyActiveRunPointerStore()
        sut = ActiveRunLockClearer(run_locator=StubRunLocator(_location("run-1")), active_run=active_run)

        with self.assertRaises(ValueError) as ctx:
            sut.clear("run-2")

        self.assertIn("run-1", str(ctx.exception))
        self.assertIn("run-2", str(ctx.exception))
        self.assertEqual(active_run.deleted, [])

    def test_clears_the_lock_when_the_run_id_matches(self):
        active_run = SpyActiveRunPointerStore()
        sut = ActiveRunLockClearer(run_locator=StubRunLocator(_location("run-1")), active_run=active_run)

        result = sut.clear("run-1")

        self.assertEqual(active_run.deleted, [Path("/runs")])
        self.assertIn("run-1", result)
        self.assertIn("/runs/run-1/events.jsonl", result)


if __name__ == "__main__":
    unittest.main()
