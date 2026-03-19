#!/usr/bin/env python3
"""Tests for validate-output.py"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "validate-output.py")
SCHEMA = str(Path(__file__).resolve().parent.parent.parent / "output.schema.json")


def run_validator(data, schema_path=SCHEMA):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        f.flush()
        result = subprocess.run(
            [sys.executable, SCRIPT, f.name, schema_path],
            capture_output=True, text=True
        )
    return result


def make_valid_input():
    return {
        "source_type": "changes",
        "metadata": {"branch": "main", "base_branch": None, "timestamp": "2026-01-01T00:00:00Z"},
        "files": [
            {
                "file_path": "Foo.swift",
                "changed_ranges": [{"start": 1, "end": 10}],
                "units": [
                    {"name": "Foo", "kind": "class", "line_start": 1, "line_end": 10, "has_changes": True}
                ]
            }
        ],
        "buffer": None,
        "detected_imports": [],
        "matched_tags": [],
        "summary": {"total_files": 1, "total_units": 1, "changed_units": 1}
    }


class TestValidateOutput(unittest.TestCase):

    def test_valid_input_passes(self):
        result = run_validator(make_valid_input())
        self.assertEqual(result.returncode, 0)
        self.assertIn("OK", result.stdout)

    def test_invalid_kind_declaration_fails(self):
        data = make_valid_input()
        data["files"][0]["units"][0]["kind"] = "declaration"
        result = run_validator(data)
        self.assertEqual(result.returncode, 1)
        self.assertIn("declaration", result.stderr)

    def test_invalid_kind_type_fails(self):
        data = make_valid_input()
        data["files"][0]["units"][0]["kind"] = "type"
        result = run_validator(data)
        self.assertEqual(result.returncode, 1)

    def test_all_valid_kinds_pass(self):
        for kind in ["class", "struct", "protocol", "enum", "extension"]:
            data = make_valid_input()
            data["files"][0]["units"][0]["kind"] = kind
            result = run_validator(data)
            self.assertEqual(result.returncode, 0, f"kind={kind} should be valid")

    def test_malformed_json_fails(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{broken")
            f.flush()
            result = subprocess.run(
                [sys.executable, SCRIPT, f.name, SCHEMA],
                capture_output=True, text=True
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("not valid JSON", result.stderr)

    def test_missing_file_fails(self):
        result = subprocess.run(
            [sys.executable, SCRIPT, "/nonexistent.json", SCHEMA],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()
