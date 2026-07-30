"""
solid-name: test_isolated_run_path_resolver
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Tests the isolation-aware base-directory decisions for provisioning and step execution.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.isolated_run_path_resolver import IsolatedRunPathResolver
from harness.isolated_run_paths import ISOLATED_RUNS_DIRNAME
from harness.startup_context import StartupContext


class TestIsolatedRunPathResolver(unittest.TestCase):

    def setUp(self):
        self.sut = IsolatedRunPathResolver()

    def test_provisioning_base_dir_is_the_startup_base_dir_when_not_isolated(self):
        startup = StartupContext(base_dir=Path("/runs"), search_paths=[])

        result = self.sut.provisioning_base_dir(startup, isolated=False)

        self.assertEqual(result, Path("/runs"))

    def test_provisioning_base_dir_is_under_the_subagents_dirname_when_isolated(self):
        startup = StartupContext(base_dir=Path("/runs"), search_paths=[])

        result = self.sut.provisioning_base_dir(startup, isolated=True)

        self.assertEqual(result, Path("/runs") / ISOLATED_RUNS_DIRNAME)

    def test_effective_base_dir_is_the_base_dir_when_not_isolated(self):
        result = self.sut.effective_base_dir(Path("/runs"), Path("/runs/run-1"), isolated=False)

        self.assertEqual(result, Path("/runs"))

    def test_effective_base_dir_is_the_run_dir_when_isolated(self):
        result = self.sut.effective_base_dir(
            Path("/runs/subagents"), Path("/runs/subagents/run-1"), isolated=True
        )

        self.assertEqual(result, Path("/runs/subagents/run-1"))


if __name__ == "__main__":
    unittest.main()
