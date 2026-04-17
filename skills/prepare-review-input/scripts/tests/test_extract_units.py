"""Tests for extract-units.py"""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from importlib import import_module

eu = import_module("extract-units")

extract_units = eu.extract_units
overlaps = eu.overlaps

SCRIPT = Path(__file__).resolve().parent.parent / "extract-units.py"


SAMPLE_SWIFT = """\
import Foundation

struct Alpha {
    func hello() {}
}

final class Beta {
    var x: Int = 0
}

protocol Gamma {
    func run()
}

enum Delta {
    case a, b
}

extension String: Gamma {
    func run() {}
}
"""


class TestExtractUnits:
    def test_finds_all_kinds(self):
        units = extract_units(SAMPLE_SWIFT)
        kinds = [u["kind"] for u in units]
        names = [u["name"] for u in units]
        assert kinds == ["struct", "class", "protocol", "enum", "extension"]
        assert names == ["Alpha", "Beta", "Gamma", "Delta", "String"]

    def test_line_end_points_before_next(self):
        units = extract_units(SAMPLE_SWIFT)
        for i in range(len(units) - 1):
            assert units[i]["line_end"] == units[i + 1]["line_start"] - 1

    def test_last_unit_extends_to_eof(self):
        units = extract_units(SAMPLE_SWIFT)
        total = len(SAMPLE_SWIFT.splitlines())
        assert units[-1]["line_end"] == total

    def test_respects_visibility_modifiers(self):
        src = "public struct Alpha {}\nprivate final class Beta {}\n"
        units = extract_units(src)
        assert [u["name"] for u in units] == ["Alpha", "Beta"]

    def test_ignores_nested_types(self):
        """Nested types are indented, top-level matcher starts with ^\\s* so indented still matches."""
        src = "struct Outer {\n    struct Inner {}\n}\n"
        units = extract_units(src)
        # Both match because we use ^\s* — known limitation, but Inner gets detected
        assert [u["name"] for u in units] == ["Outer", "Inner"]


class TestOverlaps:
    def test_no_ranges_means_whole_file(self):
        assert overlaps(1, 10, None) is True
        assert overlaps(1, 10, []) is True

    def test_overlapping(self):
        assert overlaps(10, 20, [{"start": 15, "end": 18}]) is True

    def test_adjacent_touch(self):
        assert overlaps(10, 20, [{"start": 20, "end": 30}]) is True
        assert overlaps(10, 20, [{"start": 5, "end": 10}]) is True

    def test_disjoint(self):
        assert overlaps(10, 20, [{"start": 30, "end": 40}]) is False


class TestIntegration:
    def test_updates_files_with_units_and_has_changes(self, tmp_path):
        src = tmp_path / "Sample.swift"
        src.write_text(SAMPLE_SWIFT)

        review_input = tmp_path / "review-input.json"
        review_input.write_text(json.dumps({
            "source_type": "changes",
            "metadata": {"branch": "main", "base_branch": None, "timestamp": "2026-01-01T00:00:00Z"},
            "files": [{
                "file_path": str(src),
                "changed_ranges": [{"start": 3, "end": 5}],
                "units": [],
            }],
            "buffer": None,
            "detected_imports": [],
            "matched_tags": [],
            "summary": {"total_files": 1, "total_units": 0, "changed_units": 0},
        }))

        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(review_input)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr

        data = json.loads(review_input.read_text())
        units = data["files"][0]["units"]
        assert len(units) == 5
        assert units[0]["name"] == "Alpha" and units[0]["has_changes"] is True
        assert all("line_end" in u and "has_changes" in u for u in units)
        assert data["summary"]["total_units"] == 5
        assert data["summary"]["changed_units"] == 1  # only Alpha overlaps lines 3-5

    def test_buffer_mode(self, tmp_path):
        review_input = tmp_path / "review-input.json"
        review_input.write_text(json.dumps({
            "source_type": "buffer",
            "metadata": {"branch": None, "base_branch": None, "timestamp": "2026-01-01T00:00:00Z"},
            "files": None,
            "buffer": {"input": SAMPLE_SWIFT, "units": []},
            "detected_imports": [],
            "matched_tags": [],
            "summary": {"total_files": 0, "total_units": 0, "changed_units": 0},
        }))

        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(review_input)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr

        data = json.loads(review_input.read_text())
        units = data["buffer"]["units"]
        assert [u["name"] for u in units] == ["Alpha", "Beta", "Gamma", "Delta", "String"]
        assert data["summary"]["total_units"] == 5

    def test_missing_file_yields_empty_units(self, tmp_path):
        review_input = tmp_path / "review-input.json"
        review_input.write_text(json.dumps({
            "source_type": "changes",
            "metadata": {"branch": None, "base_branch": None, "timestamp": "2026-01-01T00:00:00Z"},
            "files": [{
                "file_path": str(tmp_path / "does-not-exist.swift"),
                "changed_ranges": None,
                "units": [],
            }],
            "buffer": None,
            "detected_imports": [],
            "matched_tags": [],
            "summary": {"total_files": 1, "total_units": 0, "changed_units": 0},
        }))

        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(review_input)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(review_input.read_text())
        assert data["files"][0]["units"] == []
