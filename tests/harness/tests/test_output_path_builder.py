"""
solid-name: TestOutputPathBuilder
solid-category: unit-test
solid-spec: [SPEC-014]
solid-description: Unit tests for OutputPathBuilder. Verifies that two profiles in one run produce
separate <model> subdirectories under the same <day-time> root, and that two separate runs produce
different <day-time> directories.
"""

import tempfile
import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path

_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parents[2]
_HARNESS_DIR = _PROJECT_ROOT / "tests" / "harness"

ensure_on_path(_HARNESS_DIR, _HERE)

from output_path_builder import OutputPathBuilder


class TestOutputPathBuilder(unittest.TestCase):
    def _build(self, project_root: Path, model: str, timestamp: str) -> Path:
        return OutputPathBuilder(project_root).build(
            run_timestamp=timestamp,
            model_name=model,
            category_path="principles/SRP",
            fixture_stem="fixture-1",
            flow_name="apply",
        ).log_dir

    def test_two_profiles_same_run_share_timestamp_but_differ_in_model_segment(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            ts = "2026-06-01_12-00-00"
            claude_dir = self._build(root, "claude", ts)
            qwen_dir = self._build(root, "qwen", ts)
            self.assertIn(ts, str(claude_dir))
            self.assertIn(ts, str(qwen_dir))
            self.assertIn("claude", str(claude_dir))
            self.assertIn("qwen", str(qwen_dir))
            self.assertNotEqual(claude_dir, qwen_dir)

    def test_two_separate_runs_produce_different_timestamp_directories(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            ts1 = "2026-06-01_09-00-00"
            ts2 = "2026-06-01_10-00-00"
            dir1 = self._build(root, "claude", ts1)
            dir2 = self._build(root, "claude", ts2)
            self.assertNotEqual(dir1, dir2)
            self.assertIn(ts1, str(dir1))
            self.assertIn(ts2, str(dir2))

    def test_log_dir_is_created_on_disk(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            log_dir = self._build(root, "claude", "2026-06-01_11-00-00")
            self.assertTrue(log_dir.exists())
            self.assertTrue(log_dir.is_dir())

    def test_reasoning_path_has_fixture_stem_and_flow_in_name(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            output = OutputPathBuilder(root).build(
                run_timestamp="2026-06-01_12-00-00",
                model_name="claude",
                category_path="principles/SRP",
                fixture_stem="fixture-1",
                flow_name="apply",
            )
            self.assertIn("fixture-1", output.reasoning_path.name)
            self.assertIn("apply", output.reasoning_path.name)


if __name__ == "__main__":
    unittest.main()
