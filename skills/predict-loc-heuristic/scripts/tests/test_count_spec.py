#!/usr/bin/env python3
"""CLI contract tests for count-spec.py."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "count-spec.py"


def run(spec_text: str) -> dict:
    """Write spec_text to a temp file, invoke the script, return parsed JSON output."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        spec_file = tmp_path / "Spec.md"
        out_file = tmp_path / "heuristic.json"
        spec_file.write_text(spec_text, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(spec_file), str(out_file)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(f"script failed: {result.stderr}")
        return json.loads(out_file.read_text(encoding="utf-8"))


class CanonicalFormat(unittest.TestCase):
    def test_us_n_with_dash_bullets(self):
        spec = """# Title
## User Stories

### US-1: First story

**As a developer, I want X.**

- When A, then B
- When C, then D

### US-2: Second story

- When E, then F
"""
        out = run(spec)
        self.assertEqual(out["ac_count"], 3)
        self.assertEqual(len(out["by_story"]), 2)
        self.assertEqual(out["by_story"][0]["ac_count"], 2)
        self.assertEqual(out["by_story"][1]["ac_count"], 1)

    def test_predicted_loc_formula(self):
        spec = """## User Stories
### US-1
- A
- B
- C
"""
        out = run(spec)
        self.assertEqual(out["ac_count"], 3)
        self.assertEqual(out["predicted_loc"], 36)  # 3 × 12 + 0 × 80


class FormatTolerance(unittest.TestCase):
    def test_asterisk_bullets(self):
        spec = """## User Stories
### US-1
* When A
* When B
"""
        out = run(spec)
        self.assertEqual(out["ac_count"], 2)

    def test_plus_bullets(self):
        spec = """## User Stories
### US-1
+ When A
+ When B
+ When C
"""
        out = run(spec)
        self.assertEqual(out["ac_count"], 3)

    def test_story_n_heading(self):
        spec = """## User Stories
### Story 1: Login
- A
- B
### Story 2: Logout
- C
"""
        out = run(spec)
        self.assertEqual(out["ac_count"], 3)

    def test_scenarios_section_label(self):
        spec = """## Scenarios
### Scenario 1
- A
- B
"""
        out = run(spec)
        self.assertEqual(out["ac_count"], 2)

    def test_no_h3_subheadings(self):
        """Bullets directly under `## User Stories` count as one synthesised story."""
        spec = """## User Stories
- When A, then B
- When C, then D
- When E, then F
"""
        out = run(spec)
        self.assertEqual(out["ac_count"], 3)
        self.assertEqual(len(out["by_story"]), 1)
        self.assertEqual(out["by_story"][0]["story_id"], "(unnamed)")


class ScreenCounting(unittest.TestCase):
    def test_h3_subsections_in_ui(self):
        spec = """## User Stories
### US-1
- A
## UI / Mockup
### Login Screen
foo
### Logout Screen
bar
"""
        out = run(spec)
        self.assertEqual(out["screens"], 2)

    def test_image_references_in_ui(self):
        spec = """## User Stories
### US-1
- A
## UI / Mockup
![login](resources/login.png)
![home](resources/home.png)
"""
        out = run(spec)
        self.assertEqual(out["screens"], 2)

    def test_ui_section_with_text_only_falls_back_to_one(self):
        spec = """## User Stories
### US-1
- A
## UI / Mockup
Some text describing screens.
"""
        out = run(spec)
        self.assertEqual(out["screens"], 1)

    def test_no_ui_section(self):
        spec = """## User Stories
### US-1
- A
"""
        out = run(spec)
        self.assertEqual(out["screens"], 0)


class SeverityBands(unittest.TestCase):
    def _spec_with_n_acs(self, n: int) -> str:
        bullets = "\n".join(f"- AC {i}" for i in range(n))
        return f"## User Stories\n### US-1\n{bullets}\n"

    def test_below_minor_threshold_is_compliant(self):
        out = run(self._spec_with_n_acs(16))  # 16 × 12 = 192 < 200
        self.assertEqual(out["severity"], "COMPLIANT")

    def test_at_minor_threshold(self):
        out = run(self._spec_with_n_acs(17))  # 17 × 12 = 204 ≥ 200
        self.assertEqual(out["severity"], "MINOR")

    def test_above_severe_threshold(self):
        out = run(self._spec_with_n_acs(34))  # 34 × 12 = 408 > 400
        self.assertEqual(out["severity"], "SEVERE")


class EdgeCases(unittest.TestCase):
    def test_empty_spec_is_compliant(self):
        out = run("")
        self.assertEqual(out["ac_count"], 0)
        self.assertEqual(out["screens"], 0)
        self.assertEqual(out["severity"], "COMPLIANT")

    def test_no_user_stories_section(self):
        out = run("# Title\n## Description\nfoo bar\n")
        self.assertEqual(out["ac_count"], 0)


class CLIContract(unittest.TestCase):
    def test_missing_spec_file_exits_non_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(Path(tmp) / "missing.md"), str(Path(tmp) / "out.json")],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not found", result.stderr.lower())

    def test_wrong_arg_count_exits_non_zero(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
