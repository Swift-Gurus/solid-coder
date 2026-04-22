"""Tests for design-pattern loading behavior via paths_to_load.

Covers:
  - OCP's required_patterns are included in code/review/synth modes.
  - Planner mode does NOT include pattern files.
  - Returned pattern paths exist and are readable files.
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GATEWAY = PROJECT_ROOT / "mcp-server" / "gateway.py"


def paths_for(mode, principle="OCP"):
    r = subprocess.run(
        [sys.executable, str(GATEWAY), "load_rules",
         "--mode", mode, "--principle", principle],
        capture_output=True, text=True, cwd=PROJECT_ROOT,
    )
    if r.returncode != 0:
        raise RuntimeError(f"load_rules failed: {r.stderr}")
    return json.loads(r.stdout)["paths_to_load"]


def pattern_paths(mode, principle="OCP"):
    """Return only the design-pattern file paths (under design_patterns/)."""
    return [p for p in paths_for(mode, principle) if "design_patterns" in p]


class TestOCPRequiredPatterns(unittest.TestCase):
    def test_ocp_loads_adapter_factory_factory_method_builder_in_code_mode(self):
        pp = pattern_paths("code")
        names = [Path(p).stem for p in pp]
        self.assertIn("adapter", names)
        self.assertIn("factory", names)
        self.assertIn("factory-method", names)
        self.assertIn("builder", names)

    def test_all_pattern_paths_exist(self):
        for mode in ["code", "review", "synth-fixes"]:
            with self.subTest(mode=mode):
                for p in pattern_paths(mode):
                    self.assertTrue(Path(p).is_file(), f"{mode}: missing pattern: {p}")


class TestPlannerExcludesPatterns(unittest.TestCase):
    def test_planner_loads_no_pattern_files(self):
        pp = pattern_paths("planner")
        self.assertEqual(pp, [], f"planner must not load pattern files, got: {pp}")

    def test_planner_loads_no_code_instructions(self):
        ps = paths_for("planner")
        code_instr = [p for p in ps if "code/instructions.md" in p]
        self.assertEqual(code_instr, [],
                         f"planner must not load code/instructions.md, got: {code_instr}")


if __name__ == "__main__":
    unittest.main()
