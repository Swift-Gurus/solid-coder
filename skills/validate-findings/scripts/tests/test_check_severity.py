"""Tests for check-severity.py"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "check-severity.py"


def _write_review_output(tmp_path, principle, files):
    """Write a review-output.json for a principle with given file/unit/finding data."""
    principle_dir = tmp_path / "rules" / principle
    principle_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "agent": principle.lower(),
        "principle": principle,
        "timestamp": "2026-01-01T00:00:00Z",
        "files": files,
    }
    (principle_dir / "review-output.json").write_text(json.dumps(data))


def _make_file_entry(file_path, findings):
    """Build a file entry with a single unit containing the given findings."""
    return {
        "file": file_path,
        "units": [{
            "unit_name": "TestClass",
            "unit_kind": "class",
            "findings": findings,
        }],
    }


def _run(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(tmp_path)],
        capture_output=True, text=True,
    )
    return result


class TestCheckSeverity:
    def test_minor_only(self, tmp_path):
        _write_review_output(tmp_path, "SRP", [
            _make_file_entry("/project/Foo.swift", [
                {"id": "srp-001", "severity": "MINOR", "metric": "SRP-1",
                 "title": "t", "issue": "i"},
            ]),
        ])
        result = _run(tmp_path)
        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")
        assert lines[0] == "MINOR_ONLY"
        assert "0 severe" in lines[1]
        assert "1 minor" in lines[1]

    def test_has_severe(self, tmp_path):
        _write_review_output(tmp_path, "SRP", [
            _make_file_entry("/project/Bar.swift", [
                {"id": "srp-001", "severity": "SEVERE", "metric": "SRP-2",
                 "title": "t", "issue": "i"},
            ]),
        ])
        result = _run(tmp_path)
        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")
        assert lines[0] == "HAS_SEVERE"
        assert "1 severe" in lines[1]

    def test_no_findings(self, tmp_path):
        _write_review_output(tmp_path, "SRP", [
            {"file": "/project/Clean.swift", "units": [{
                "unit_name": "CleanClass", "unit_kind": "class", "findings": [],
            }]},
        ])
        result = _run(tmp_path)
        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")
        assert lines[0] == "MINOR_ONLY"
        assert "0 findings" in lines[1]

    def test_mixed_severities(self, tmp_path):
        _write_review_output(tmp_path, "SRP", [
            _make_file_entry("/project/Foo.swift", [
                {"id": "srp-001", "severity": "MINOR", "metric": "SRP-1",
                 "title": "t", "issue": "i"},
            ]),
        ])
        _write_review_output(tmp_path, "OCP", [
            _make_file_entry("/project/Foo.swift", [
                {"id": "ocp-001", "severity": "SEVERE", "metric": "OCP-1",
                 "title": "t", "issue": "i"},
            ]),
        ])
        result = _run(tmp_path)
        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")
        assert lines[0] == "HAS_SEVERE"
        assert "1 severe" in lines[1]
        assert "1 minor" in lines[1]

    def test_missing_rules_dir(self, tmp_path):
        result = _run(tmp_path)
        assert result.returncode == 1
        assert "not found" in result.stderr

    def test_multiple_principles_minor_only(self, tmp_path):
        _write_review_output(tmp_path, "SRP", [
            _make_file_entry("/project/Foo.swift", [
                {"id": "srp-001", "severity": "MINOR", "metric": "SRP-1",
                 "title": "t", "issue": "i"},
            ]),
        ])
        _write_review_output(tmp_path, "OCP", [
            _make_file_entry("/project/Foo.swift", [
                {"id": "ocp-001", "severity": "MINOR", "metric": "OCP-1",
                 "title": "t", "issue": "i"},
            ]),
        ])
        _write_review_output(tmp_path, "LSP", [
            {"file": "/project/Foo.swift", "units": [{
                "unit_name": "Foo", "unit_kind": "class", "findings": [],
            }]},
        ])
        result = _run(tmp_path)
        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")
        assert lines[0] == "MINOR_ONLY"
        assert "2 minor" in lines[1]
        assert "3 principles" in lines[1]
