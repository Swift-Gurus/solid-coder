#!/usr/bin/env python3
"""Tests for load-context.py"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

_LOAD_CONTEXT_SCRIPT = os.path.join(os.path.dirname(__file__), "load-context.py")


def _write_load_context_fixture(by_file_dir: str, filename: str, principles: list) -> None:
    """Write a by-file output JSON for load-context.py tests."""
    json.dump(
        {
            "file_path": f"/project/{filename.replace('.output.json', '')}",
            "timestamp": "2026-04-03T00:00:00Z",
            "principles": principles,
        },
        open(os.path.join(by_file_dir, filename), "w"),
    )


class TestLoadContext(unittest.TestCase):

    def _run(self, *args):
        return subprocess.run(
            [sys.executable, _LOAD_CONTEXT_SCRIPT, *args],
            capture_output=True, text=True,
        )

    def test_no_args(self):
        r = self._run()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Usage", r.stderr)

    def test_missing_dir(self):
        r = self._run("/nonexistent/path")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not found", r.stderr)

    def test_empty_by_file_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "by-file"))
            data = json.loads(self._run(tmp).stdout)
            self.assertTrue(data["all_compliant"])
            self.assertEqual(data["files"], [])
            self.assertEqual(data["active_principles"], [])
            self.assertEqual(data["summary"]["total_files"], 0)

    def test_no_by_file_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = json.loads(self._run(tmp).stdout)
            self.assertTrue(data["all_compliant"])

    def test_all_compliant(self):
        with tempfile.TemporaryDirectory() as tmp:
            by_file = os.path.join(tmp, "by-file")
            os.makedirs(by_file)
            _write_load_context_fixture(by_file, "Foo.swift.output.json", [
                {"principle": "SRP", "severity": "COMPLIANT", "violations": [], "suggestions": []},
            ])
            data = json.loads(self._run(tmp).stdout)
            self.assertTrue(data["all_compliant"])
            self.assertEqual(data["active_principles"], [])
            self.assertEqual(data["summary"]["total_violations"], 0)

    def test_single_violation(self):
        with tempfile.TemporaryDirectory() as tmp:
            by_file = os.path.join(tmp, "by-file")
            os.makedirs(by_file)
            _write_load_context_fixture(by_file, "Bar.swift.output.json", [
                {
                    "principle": "OCP",
                    "severity": "SEVERE",
                    "violations": [{"rule_id": "OCP-1", "severity": "SEVERE"}],
                    "suggestions": [
                        {"id": "fix-001", "addresses": ["OCP-1"],
                         "severity": "SEVERE", "suggested_fix": "...", "todo_items": ["step1"]}
                    ],
                }
            ])
            data = json.loads(self._run(tmp).stdout)
            self.assertFalse(data["all_compliant"])
            self.assertEqual(data["active_principles"], ["OCP"])
            self.assertEqual(data["summary"]["total_violations"], 1)
            self.assertEqual(data["summary"]["severe_count"], 1)
            self.assertEqual(data["summary"]["files_with_violations"], 1)
            p = data["files"][0]["principles"][0]
            self.assertEqual(p["violation_ids"], ["OCP-1"])
            self.assertTrue(p["has_suggestions"])

    def test_multiple_principles_multiple_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            by_file = os.path.join(tmp, "by-file")
            os.makedirs(by_file)
            _write_load_context_fixture(by_file, "A.swift.output.json", [
                {
                    "principle": "SRP", "severity": "SEVERE",
                    "violations": [
                        {"rule_id": "SRP-1", "severity": "SEVERE"},
                        {"rule_id": "SRP-2", "severity": "MINOR"},
                    ],
                    "suggestions": [],
                },
                {"principle": "OCP", "severity": "COMPLIANT", "violations": [], "suggestions": []},
            ])
            _write_load_context_fixture(by_file, "B.swift.output.json", [
                {
                    "principle": "SwiftUI", "severity": "SEVERE",
                    "violations": [{"rule_id": "SUI-1", "severity": "SEVERE"}],
                    "suggestions": [],
                },
            ])
            data = json.loads(self._run(tmp).stdout)
            self.assertFalse(data["all_compliant"])
            self.assertEqual(sorted(data["active_principles"]), ["SRP", "SwiftUI"])
            self.assertEqual(data["summary"]["total_files"], 2)
            self.assertEqual(data["summary"]["files_with_violations"], 2)
            self.assertEqual(data["summary"]["total_violations"], 3)
            self.assertEqual(data["summary"]["severe_count"], 2)
            self.assertEqual(data["summary"]["minor_count"], 1)
            self.assertEqual(data["summary"]["principles_with_violations"], 2)

    def test_malformed_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            by_file = os.path.join(tmp, "by-file")
            os.makedirs(by_file)
            with open(os.path.join(by_file, "Bad.swift.output.json"), "w") as f:
                f.write("{invalid json")
            r = self._run(tmp)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("ERROR", r.stderr)

    def test_compliant_principle_not_in_active(self):
        with tempfile.TemporaryDirectory() as tmp:
            by_file = os.path.join(tmp, "by-file")
            os.makedirs(by_file)
            _write_load_context_fixture(by_file, "C.swift.output.json", [
                {
                    "principle": "SRP", "severity": "SEVERE",
                    "violations": [{"rule_id": "SRP-1", "severity": "SEVERE"}],
                    "suggestions": [],
                },
                {"principle": "LSP", "severity": "COMPLIANT", "violations": [], "suggestions": []},
            ])
            data = json.loads(self._run(tmp).stdout)
            self.assertEqual(data["active_principles"], ["SRP"])


if __name__ == "__main__":
    unittest.main()
