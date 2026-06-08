"""Tests for validate-findings.py"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Add parent dir to path so we can import the module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from importlib import import_module

vf = import_module("validate-findings")

unit_in_changed_range = vf.unit_in_changed_range
worst_severity = vf.worst_severity
_unit_passes_filter = vf._unit_passes_filter
_match_suggestions = vf._match_suggestions

SCRIPT = Path(__file__).resolve().parent.parent / "validate-findings.py"
PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


# ---------- unit_in_changed_range ----------

class TestUnitInChangedRange:
    def _unit(self, line_start=None, line_end=None):
        u = {}
        if line_start is not None:
            u["line_start"] = line_start
        if line_end is not None:
            u["line_end"] = line_end
        return u

    def test_overlap_exact(self):
        unit = self._unit(10, 20)
        assert unit_in_changed_range(unit, [{"start": 10, "end": 20}]) is True

    def test_overlap_partial(self):
        unit = self._unit(10, 20)
        assert unit_in_changed_range(unit, [{"start": 15, "end": 25}]) is True

    def test_no_overlap(self):
        unit = self._unit(10, 20)
        assert unit_in_changed_range(unit, [{"start": 25, "end": 30}]) is False

    def test_missing_line_start(self):
        unit = self._unit(line_end=20)
        assert unit_in_changed_range(unit, [{"start": 25, "end": 30}]) is True

    def test_missing_line_end(self):
        unit = self._unit(line_start=10)
        assert unit_in_changed_range(unit, [{"start": 25, "end": 30}]) is True

    def test_empty_ranges(self):
        unit = self._unit(10, 20)
        assert unit_in_changed_range(unit, []) is False

    def test_adjacent_not_overlapping(self):
        unit = self._unit(10, 20)
        assert unit_in_changed_range(unit, [{"start": 21, "end": 30}]) is False

    def test_adjacent_touching(self):
        unit = self._unit(10, 20)
        assert unit_in_changed_range(unit, [{"start": 20, "end": 30}]) is True

    def test_multiple_ranges_second_overlaps(self):
        unit = self._unit(50, 60)
        ranges = [{"start": 1, "end": 10}, {"start": 55, "end": 70}]
        assert unit_in_changed_range(unit, ranges) is True


# ---------- worst_severity ----------

class TestWorstSeverity:
    def test_empty_list(self):
        assert worst_severity([]) == "COMPLIANT"

    def test_single_minor(self):
        assert worst_severity([{"severity": "MINOR"}]) == "MINOR"

    def test_single_severe(self):
        assert worst_severity([{"severity": "SEVERE"}]) == "SEVERE"

    def test_mixed(self):
        violations = [
            {"severity": "MINOR"},
            {"severity": "SEVERE"},
            {"severity": "COMPLIANT"},
        ]
        assert worst_severity(violations) == "SEVERE"

    def test_all_compliant(self):
        violations = [{"severity": "COMPLIANT"}, {"severity": "COMPLIANT"}]
        assert worst_severity(violations) == "COMPLIANT"

    def test_missing_severity_key(self):
        violations = [{"rule_id": "SRP-1"}]
        assert worst_severity(violations) == "COMPLIANT"


# ---------- _unit_passes_filter ----------

class TestUnitPassesFilter:
    def _unit(self, line_start=None, line_end=None):
        u = {}
        if line_start is not None:
            u["line_start"] = line_start
        if line_end is not None:
            u["line_end"] = line_end
        return u

    def test_skip_filtering_passes_all(self):
        unit = self._unit(100, 200)
        assert _unit_passes_filter(unit, "/some/file.swift", {}, True) is True

    def test_null_changed_ranges_passes(self):
        unit = self._unit(10, 20)
        lookup = {"/file.swift": None}
        assert _unit_passes_filter(unit, "/file.swift", lookup, False) is True

    def test_true_changed_ranges_passes(self):
        unit = self._unit(10, 20)
        lookup = {"/file.swift": True}
        assert _unit_passes_filter(unit, "/file.swift", lookup, False) is True

    def test_file_not_in_lookup_passes(self):
        unit = self._unit(10, 20)
        assert _unit_passes_filter(unit, "/file.swift", {}, False) is False

    def test_list_ranges_overlap_passes(self):
        unit = self._unit(10, 20)
        lookup = {"/file.swift": [{"start": 15, "end": 25}]}
        assert _unit_passes_filter(unit, "/file.swift", lookup, False) is True

    def test_list_ranges_no_overlap_fails(self):
        unit = self._unit(10, 20)
        lookup = {"/file.swift": [{"start": 50, "end": 60}]}
        assert _unit_passes_filter(unit, "/file.swift", lookup, False) is False


# ---------- _match_suggestions ----------

class TestMatchSuggestions:
    def test_no_suggestions(self):
        violations = [{"rule_id": "SRP-1", "severity": "SEVERE"}]
        result = _match_suggestions(violations, {})
        assert result == []

    def test_matching_suggestion(self):
        violations = [{"rule_id": "SRP-1", "severity": "SEVERE"}]
        suggestions_by_rule = {
            "SRP-1": [{"id": "fix-001", "addresses": ["SRP-1"]}]
        }
        result = _match_suggestions(violations, suggestions_by_rule)
        assert len(result) == 1
        assert result[0]["id"] == "fix-001"

    def test_deduplication(self):
        violations = [
            {"rule_id": "SRP-1", "severity": "SEVERE"},
            {"rule_id": "SRP-2", "severity": "SEVERE"},
        ]
        shared = {"id": "fix-001", "addresses": ["SRP-1", "SRP-2"]}
        suggestions_by_rule = {"SRP-1": [shared], "SRP-2": [shared]}
        result = _match_suggestions(violations, suggestions_by_rule)
        assert len(result) == 1  # deduplicated

    def test_multiple_suggestions(self):
        violations = [
            {"rule_id": "SRP-1", "severity": "SEVERE"},
            {"rule_id": "SRP-2", "severity": "SEVERE"},
        ]
        suggestions_by_rule = {
            "SRP-1": [{"id": "fix-001", "addresses": ["SRP-1"]}],
            "SRP-2": [{"id": "fix-002", "addresses": ["SRP-2"]}],
        }
        result = _match_suggestions(violations, suggestions_by_rule)
        assert len(result) == 2


# ---------- Integration ----------

def _build_review_input(source_type="folder"):
    return {
        "source_type": source_type,
        "metadata": {"branch": None, "base_branch": None, "timestamp": "2026-01-01T00:00:00Z"},
        "files": [
            {
                "file_path": "/project/MyFile.swift",
                "changed_ranges": None,
                "units": [
                    {"name": "MyClass", "kind": "class", "line_start": 1, "line_end": 50}
                ],
            }
        ],
        "buffer": None,
        "summary": {"total_files": 1, "total_units": 1, "changed_units": 1},
    }


def _build_review_output():
    """Build a new-format review output with SRP violations."""
    return {
        "timestamp": "2026-01-01T00:00:00Z",
        "files": [
            {
                "file_path": "/project/MyFile.swift",
                "units": [
                    {
                        "unit_name": "MyClass",
                        "unit_kind": "class",
                        "line_start": 1,
                        "line_end": 50,
                        "metrics": {
                            "SRP": {
                                "verb_count":        {"value": 4},
                                "cohesion_groups":   {"value": 2},
                                "stakeholder_count": {"value": 2},
                            }
                        },
                        "violations": [
                            {"rule_id": "SRP-1", "severity": "SEVERE"},
                            {"rule_id": "SRP-2", "severity": "SEVERE"},
                        ],
                    }
                ],
            }
        ],
    }


class TestIntegration:
    def test_end_to_end(self, tmp_path):
        """Build minimal output-root, run script, verify by-file output."""
        prepare_dir = tmp_path / "prepare"
        prepare_dir.mkdir()
        rules_dir = tmp_path / "rules" / "srp"
        rules_dir.mkdir(parents=True)

        review_input = _build_review_input()
        (prepare_dir / "review-input.json").write_text(json.dumps(review_input))

        review_output = _build_review_output()
        (rules_dir / "review-output.json").write_text(json.dumps(review_output))

        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(tmp_path)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

        by_file = tmp_path / "by-file"
        assert by_file.exists()
        outputs = list(by_file.glob("*.output.json"))
        assert len(outputs) == 1

        data = json.loads(outputs[0].read_text())
        assert data["file_path"] == "/project/MyFile.swift"
        assert len(data["principles"]) == 1
        assert data["principles"][0]["severity"] == "SEVERE"

    def test_schema_validation_passes_for_new_format(self, tmp_path):
        """When plugin-root is provided, valid new-format JSON should succeed."""
        prepare_dir = tmp_path / "prepare"
        prepare_dir.mkdir()
        rules_dir = tmp_path / "rules" / "srp"
        rules_dir.mkdir(parents=True)

        review_input = _build_review_input()
        (prepare_dir / "review-input.json").write_text(json.dumps(review_input))

        review_output = _build_review_output()
        (rules_dir / "review-output.json").write_text(json.dumps(review_output))

        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(tmp_path), str(PLUGIN_ROOT)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_no_plugin_root_skips_validation(self, tmp_path):
        """Without plugin-root, output is processed regardless of exact schema shape."""
        prepare_dir = tmp_path / "prepare"
        prepare_dir.mkdir()
        rules_dir = tmp_path / "rules" / "srp"
        rules_dir.mkdir(parents=True)

        review_input = _build_review_input()
        (prepare_dir / "review-input.json").write_text(json.dumps(review_input))

        review_output = _build_review_output()
        (rules_dir / "review-output.json").write_text(json.dumps(review_output))

        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(tmp_path)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
