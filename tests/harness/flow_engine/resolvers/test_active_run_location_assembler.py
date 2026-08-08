"""
solid-name: test_active_run_location_assembler
solid-category: unit-test
solid-spec: [SPEC-031]
solid-description: Tests building an ActiveRunLocation from a run's identity and directories.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.active_run_location_assembler import ActiveRunLocationAssembler


class TestActiveRunLocationAssembler(unittest.TestCase):

    def setUp(self):
        self.sut = ActiveRunLocationAssembler()

    def test_assembles_a_location_with_derived_events_and_workflow_paths(self):
        result = self.sut.assemble("run-1", Path("/runs"), Path("/runs/run-1"))

        self.assertEqual(result.run_id, "run-1")
        self.assertEqual(result.base_dir, Path("/runs"))
        self.assertEqual(result.run_dir, Path("/runs/run-1"))
        self.assertEqual(result.events_path, str(Path("/runs/run-1/events.jsonl")))
        self.assertEqual(result.workflow_path, str(Path("/runs/run-1/workflow.yaml")))


if __name__ == "__main__":
    unittest.main()
