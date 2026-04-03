#!/usr/bin/env python3
"""Tests for load-context.py"""

import json
import os
import subprocess
import sys
import tempfile
import unittest


SCRIPT = os.path.join(os.path.dirname(__file__), "load-context.py")


def run_script(*args):
    result = subprocess.run(
        [sys.executable, SCRIPT, *args],
        capture_output=True,
        text=True,
    )
    return result


def make_output_file(by_file_dir, filename, principles):
    """Create a by-file/*.output.json with given principles data."""
    data = {
        "file_path": f"/project/Sources/{filename.replace('.output.json', '')}",
        "timestamp": "2026-04-03T00:00:00Z",
        "principles": principles,
    }
    path = os.path.join(by_file_dir, filename)
    with open(path, "w") as f:
        json.dump(data, f)
    return path


class TestLoadContext(unittest.TestCase):

    def test_no_args(self):
        r = run_script()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Usage", r.stderr)

    def test_missing_dir(self):
        r = run_script("/nonexistent/path")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not found", r.stderr)

    def test_empty_by_file_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            by_file = os.path.join(tmp, "by-file")
            os.makedirs(by_file)
            r = run_script(tmp)
            self.assertEqual(r.returncode, 0)
            data = json.loads(r.stdout)
            self.assertTrue(data["all_compliant"])
            self.assertEqual(data["files"], [])
            self.assertEqual(data["active_principles"], [])
            self.assertEqual(data["summary"]["total_files"], 0)

    def test_no_by_file_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run_script(tmp)
            self.assertEqual(r.returncode, 0)
            data = json.loads(r.stdout)
            self.assertTrue(data["all_compliant"])

    def test_all_compliant(self):
        with tempfile.TemporaryDirectory() as tmp:
            by_file = os.path.join(tmp, "by-file")
            os.makedirs(by_file)
            make_output_file(by_file, "Foo.swift.output.json", [
                {
                    "agent": "srp",
                    "principle": "Single Responsibility",
                    "severity": "COMPLIANT",
                    "findings": [],
                    "suggestions": [],
                }
            ])
            r = run_script(tmp)
            self.assertEqual(r.returncode, 0)
            data = json.loads(r.stdout)
            self.assertTrue(data["all_compliant"])
            self.assertEqual(len(data["files"]), 1)
            self.assertEqual(data["active_principles"], [])
            self.assertEqual(data["summary"]["total_findings"], 0)

    def test_single_finding(self):
        with tempfile.TemporaryDirectory() as tmp:
            by_file = os.path.join(tmp, "by-file")
            os.makedirs(by_file)
            make_output_file(by_file, "Bar.swift.output.json", [
                {
                    "agent": "ocp",
                    "principle": "Open/Closed",
                    "severity": "SEVERE",
                    "findings": [
                        {"id": "ocp-001", "severity": "SEVERE", "metric": "OCP-1",
                         "title": "Sealed point", "issue": "Direct construction"}
                    ],
                    "suggestions": [
                        {"id": "ocp-fix-001", "addresses": ["ocp-001"],
                         "title": "Inject", "severity": "SEVERE",
                         "suggested_fix": "...", "todo_items": ["step1"]}
                    ],
                }
            ])
            r = run_script(tmp)
            self.assertEqual(r.returncode, 0)
            data = json.loads(r.stdout)
            self.assertFalse(data["all_compliant"])
            self.assertEqual(data["active_principles"], ["ocp"])
            self.assertEqual(data["summary"]["total_findings"], 1)
            self.assertEqual(data["summary"]["severe_count"], 1)
            self.assertEqual(data["summary"]["files_with_findings"], 1)
            # Check file-level detail
            file_data = data["files"][0]
            self.assertEqual(file_data["principles"][0]["finding_ids"], ["ocp-001"])
            self.assertTrue(file_data["principles"][0]["has_suggestions"])

    def test_multiple_principles_multiple_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            by_file = os.path.join(tmp, "by-file")
            os.makedirs(by_file)
            make_output_file(by_file, "A.swift.output.json", [
                {
                    "agent": "srp",
                    "principle": "Single Responsibility",
                    "severity": "SEVERE",
                    "findings": [
                        {"id": "srp-001", "severity": "SEVERE", "metric": "SRP-1",
                         "title": "t", "issue": "i"},
                        {"id": "srp-002", "severity": "MINOR", "metric": "SRP-2",
                         "title": "t", "issue": "i"},
                    ],
                    "suggestions": [],
                },
                {
                    "agent": "ocp",
                    "principle": "Open/Closed",
                    "severity": "COMPLIANT",
                    "findings": [],
                    "suggestions": [],
                },
            ])
            make_output_file(by_file, "B.swift.output.json", [
                {
                    "agent": "swiftui",
                    "principle": "SwiftUI Best Practices",
                    "severity": "SEVERE",
                    "findings": [
                        {"id": "sui-001", "severity": "SEVERE", "metric": "SUI-1",
                         "title": "t", "issue": "i"},
                    ],
                    "suggestions": [],
                },
            ])
            r = run_script(tmp)
            self.assertEqual(r.returncode, 0)
            data = json.loads(r.stdout)
            self.assertFalse(data["all_compliant"])
            self.assertEqual(sorted(data["active_principles"]), ["srp", "swiftui"])
            self.assertEqual(data["summary"]["total_files"], 2)
            self.assertEqual(data["summary"]["files_with_findings"], 2)
            self.assertEqual(data["summary"]["total_findings"], 3)
            self.assertEqual(data["summary"]["severe_count"], 2)
            self.assertEqual(data["summary"]["minor_count"], 1)
            self.assertEqual(data["summary"]["principles_with_findings"], 2)

    def test_malformed_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            by_file = os.path.join(tmp, "by-file")
            os.makedirs(by_file)
            bad_file = os.path.join(by_file, "Bad.swift.output.json")
            with open(bad_file, "w") as f:
                f.write("{invalid json")
            r = run_script(tmp)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("ERROR", r.stderr)

    def test_compliant_principle_not_in_active(self):
        """Principles with COMPLIANT severity should not appear in active_principles."""
        with tempfile.TemporaryDirectory() as tmp:
            by_file = os.path.join(tmp, "by-file")
            os.makedirs(by_file)
            make_output_file(by_file, "C.swift.output.json", [
                {
                    "agent": "srp",
                    "principle": "Single Responsibility",
                    "severity": "SEVERE",
                    "findings": [
                        {"id": "srp-001", "severity": "SEVERE", "metric": "SRP-1",
                         "title": "t", "issue": "i"}
                    ],
                    "suggestions": [],
                },
                {
                    "agent": "lsp",
                    "principle": "Liskov Substitution",
                    "severity": "COMPLIANT",
                    "findings": [],
                    "suggestions": [],
                },
            ])
            r = run_script(tmp)
            data = json.loads(r.stdout)
            self.assertEqual(data["active_principles"], ["srp"])


if __name__ == "__main__":
    unittest.main()
