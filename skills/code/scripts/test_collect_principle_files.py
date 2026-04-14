#!/usr/bin/env python3
"""Tests for collect-principle-files.py."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPT = SCRIPT_DIR / "collect-principle-files.py"
DISCOVER_SCRIPT = (
    SCRIPT_DIR.parent.parent / "discover-principles" / "scripts" / "discover-principles.py"
)
REFS_ROOT = SCRIPT_DIR.parent.parent.parent / "references"


def run_script(input_json: str) -> dict:
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=input_json,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Script failed: {result.stderr}")
    return json.loads(result.stdout)


def run_discover(extra_args: list = None) -> dict:
    cmd = [sys.executable, str(DISCOVER_SCRIPT), "--refs-root", str(REFS_ROOT)]
    if extra_args:
        cmd.extend(extra_args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Discover failed: {result.stderr}")
    return json.loads(result.stdout)


class TestCollectPrincipleFiles(unittest.TestCase):

    def test_output_has_files_to_load_key(self):
        discover = run_discover()
        output = run_script(json.dumps(discover))
        self.assertIn("files_to_load", output)
        self.assertIsInstance(output["files_to_load"], list)

    def test_all_paths_are_absolute(self):
        discover = run_discover()
        output = run_script(json.dumps(discover))
        for path in output["files_to_load"]:
            self.assertTrue(
                Path(path).is_absolute(),
                f"Path is not absolute: {path}",
            )

    def test_all_paths_exist(self):
        discover = run_discover()
        output = run_script(json.dumps(discover))
        for path in output["files_to_load"]:
            self.assertTrue(
                Path(path).is_file(),
                f"File does not exist: {path}",
            )

    def test_no_duplicate_paths(self):
        discover = run_discover()
        output = run_script(json.dumps(discover))
        files = output["files_to_load"]
        self.assertEqual(len(files), len(set(files)), "Duplicate paths found")

    def test_includes_rule_md_for_each_principle(self):
        discover = run_discover()
        output = run_script(json.dumps(discover))
        files = output["files_to_load"]
        for principle in discover["active_principles"]:
            self.assertIn(
                principle["rule_path"],
                files,
                f"Missing rule.md for {principle['name']}",
            )

    def test_includes_fix_instructions_for_each_principle(self):
        discover = run_discover()
        output = run_script(json.dumps(discover))
        files = output["files_to_load"]
        for principle in discover["active_principles"]:
            fix_path = str(Path(principle["folder"]) / "fix" / "instructions.md")
            if Path(fix_path).is_file():
                self.assertIn(
                    fix_path,
                    files,
                    f"Missing fix/instructions.md for {principle['name']}",
                )

    def test_accepts_full_discover_output(self):
        discover = run_discover()
        output = run_script(json.dumps(discover))
        self.assertGreater(len(output["files_to_load"]), 0)

    def test_accepts_bare_array(self):
        discover = run_discover()
        output = run_script(json.dumps(discover["active_principles"]))
        self.assertGreater(len(output["files_to_load"]), 0)

    def test_tag_filtering_reduces_files(self):
        all_output = run_script(json.dumps(run_discover()))
        filtered_output = run_script(
            json.dumps(run_discover(["--matched-tags", "swiftui"]))
        )
        self.assertGreater(
            len(all_output["files_to_load"]),
            len(filtered_output["files_to_load"]),
        )

    def test_empty_principles_returns_empty(self):
        output = run_script(json.dumps([]))
        self.assertEqual(output["files_to_load"], [])

    def test_file_flag(self):
        import tempfile
        discover = run_discover()
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(discover, f)
            f.flush()
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--file", f.name],
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertGreater(len(output["files_to_load"]), 0)
        Path(f.name).unlink()

    def test_json_flag(self):
        discover = run_discover()
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--json", json.dumps(discover)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertGreater(len(output["files_to_load"]), 0)


if __name__ == "__main__":
    unittest.main()
