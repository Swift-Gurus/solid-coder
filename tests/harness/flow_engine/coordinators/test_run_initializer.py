"""Tests run-directory provisioning and active-pointer ownership."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.models import FlowDef  # noqa: E402
from harness.run_initializer import RunInitializer  # noqa: E402


class SpyActiveRunPointer:
    def __init__(self) -> None:
        self.writes: list[tuple[Path, str]] = []

    def read(self, base_dir: Path) -> str:
        raise NotImplementedError

    def write(self, base_dir: Path, run_id: str) -> None:
        self.writes.append((base_dir, run_id))

    def delete(self, base_dir: Path) -> None:
        raise NotImplementedError


class StubRunDirectoryScaffolder:
    def scaffold(self, base_dir: Path, run_id: str, flow_def: FlowDef) -> Path:
        return base_dir / run_id


"""
solid-name: TestRunInitializer
solid-category: unit-test
solid-spec: [SPEC-031, SPEC-047]
solid-description: Verifies only normal session-owned runs create active-run pointers.
"""
class TestRunInitializer(unittest.TestCase):
    def setUp(self) -> None:
        self.active_run = SpyActiveRunPointer()
        self.sut = RunInitializer(
            active_run=self.active_run,
            scaffolder=StubRunDirectoryScaffolder(),
            run_id_factory=lambda: "run-1",
        )
        self.flow = FlowDef(name="Review", max_turns=2, steps=[])

    def test_normal_run_registers_session_scoped_active_pointer(self) -> None:
        result = self.sut.initialize(Path("/runs"), self.flow)

        self.assertEqual(
            self.active_run.writes,
            [(Path("/runs"), "run-1")],
        )
        self.assertEqual(result.run_id, "run-1")

    def test_isolated_run_does_not_register_active_pointer(self) -> None:
        self.sut.initialize(Path("/runs/subagents"), self.flow, self_contained=True)

        self.assertEqual(self.active_run.writes, [])


if __name__ == "__main__":
    unittest.main()
