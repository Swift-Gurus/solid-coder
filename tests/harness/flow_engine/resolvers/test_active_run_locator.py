"""
solid-name: test_active_run_locator
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Tests deriving the active run's directory and file paths from its id.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.active_run_locator import ActiveRunLocator


class StubBaseDirResolver:
    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir

    def resolve(self) -> Path:
        return self._base_dir


class StubActiveRunPointer:
    def __init__(self, run_id: str) -> None:
        self._run_id = run_id

    def read(self, base_dir: Path) -> str:
        return self._run_id

    def write(self, base_dir: Path, run_id: str) -> None:
        raise NotImplementedError

    def delete(self, base_dir: Path) -> None:
        raise NotImplementedError


class TestActiveRunLocator(unittest.TestCase):

    def test_locates_run_dir_and_file_paths_from_active_run_id(self):
        base_dir = Path("/runs")
        sut = ActiveRunLocator(
            base_dir_resolver=StubBaseDirResolver(base_dir),
            active_run=StubActiveRunPointer("run-123"),
        )

        location = sut.locate()

        self.assertEqual(location.run_id, "run-123")
        self.assertEqual(location.base_dir, base_dir)
        self.assertEqual(location.run_dir, base_dir / "run-123")
        self.assertEqual(location.events_path, str(base_dir / "run-123" / "events.jsonl"))
        self.assertEqual(location.workflow_path, str(base_dir / "run-123" / "workflow.yaml"))

    def test_locates_an_isolated_run_self_contained_by_run_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            isolated_dir = base_dir / "subagents" / "run-abc"
            isolated_dir.mkdir(parents=True)
            (isolated_dir / "active.json").write_text('{"run_id": "run-abc"}')
            sut = ActiveRunLocator(
                base_dir_resolver=StubBaseDirResolver(base_dir),
                active_run=StubActiveRunPointer("main-run"),
            )

            location = sut.locate("run-abc")

            self.assertEqual(location.run_id, "run-abc")
            self.assertEqual(location.base_dir, isolated_dir)
            self.assertEqual(location.run_dir, isolated_dir)
            self.assertEqual(location.events_path, str(isolated_dir / "events.jsonl"))
            self.assertEqual(location.workflow_path, str(isolated_dir / "workflow.yaml"))

    def test_raises_file_not_found_when_isolated_run_does_not_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            base_dir = Path(tmp)
            sut = ActiveRunLocator(
                base_dir_resolver=StubBaseDirResolver(base_dir),
                active_run=StubActiveRunPointer("main-run"),
            )

            with self.assertRaises(FileNotFoundError):
                sut.locate("missing-run")


if __name__ == "__main__":
    unittest.main()
