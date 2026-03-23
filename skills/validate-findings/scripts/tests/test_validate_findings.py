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

ranges_overlap = vf.ranges_overlap
worst_severity = vf.worst_severity
_filter_findings = vf._filter_findings
_match_suggestions = vf._match_suggestions

SCRIPT = Path(__file__).resolve().parent.parent / "validate-findings.py"
PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


# ---------- ranges_overlap ----------

class TestRangesOverlap:
    def test_overlap_exact(self):
        finding = {"line_start": 10, "line_end": 20}
        ranges = [{"start": 10, "end": 20}]
        assert ranges_overlap(finding, ranges) is True

    def test_overlap_partial(self):
        finding = {"line_start": 10, "line_end": 20}
        ranges = [{"start": 15, "end": 25}]
        assert ranges_overlap(finding, ranges) is True

    def test_no_overlap(self):
        finding = {"line_start": 10, "line_end": 20}
        ranges = [{"start": 25, "end": 30}]
        assert ranges_overlap(finding, ranges) is False

    def test_missing_line_start(self):
        finding = {"line_end": 20}
        ranges = [{"start": 25, "end": 30}]
        assert ranges_overlap(finding, ranges) is True  # no line info = keep

    def test_missing_line_end(self):
        finding = {"line_start": 10}
        ranges = [{"start": 25, "end": 30}]
        assert ranges_overlap(finding, ranges) is True

    def test_empty_ranges(self):
        finding = {"line_start": 10, "line_end": 20}
        assert ranges_overlap(finding, []) is False

    def test_adjacent_not_overlapping(self):
        finding = {"line_start": 10, "line_end": 20}
        ranges = [{"start": 21, "end": 30}]
        assert ranges_overlap(finding, ranges) is False

    def test_adjacent_touching(self):
        finding = {"line_start": 10, "line_end": 20}
        ranges = [{"start": 20, "end": 30}]
        assert ranges_overlap(finding, ranges) is True

    def test_multiple_ranges_second_overlaps(self):
        finding = {"line_start": 50, "line_end": 60}
        ranges = [{"start": 1, "end": 10}, {"start": 55, "end": 70}]
        assert ranges_overlap(finding, ranges) is True


# ---------- worst_severity ----------

class TestWorstSeverity:
    def test_empty_list(self):
        assert worst_severity([]) == "COMPLIANT"

    def test_single_minor(self):
        assert worst_severity([{"severity": "MINOR"}]) == "MINOR"

    def test_single_severe(self):
        assert worst_severity([{"severity": "SEVERE"}]) == "SEVERE"

    def test_mixed(self):
        findings = [
            {"severity": "MINOR"},
            {"severity": "SEVERE"},
            {"severity": "COMPLIANT"},
        ]
        assert worst_severity(findings) == "SEVERE"

    def test_all_compliant(self):
        findings = [{"severity": "COMPLIANT"}, {"severity": "COMPLIANT"}]
        assert worst_severity(findings) == "COMPLIANT"

    def test_missing_severity_key(self):
        findings = [{"id": "srp-001"}]
        assert worst_severity(findings) == "COMPLIANT"


# ---------- _filter_findings ----------

class TestFilterFindings:
    def test_skip_filtering_passes_all(self):
        findings = [{"id": "a", "line_start": 100, "line_end": 200}]
        result = _filter_findings(findings, "/some/file.swift", {}, True)
        assert result == findings

    def test_null_changed_ranges_passes_all(self):
        findings = [{"id": "a", "line_start": 10, "line_end": 20}]
        lookup = {"/file.swift": None}
        result = _filter_findings(findings, "/file.swift", lookup, False)
        assert result == findings

    def test_true_changed_ranges_passes_all(self):
        findings = [{"id": "a", "line_start": 10, "line_end": 20}]
        lookup = {"/file.swift": True}
        result = _filter_findings(findings, "/file.swift", lookup, False)
        assert result == findings

    def test_file_not_in_lookup_passes_all(self):
        findings = [{"id": "a", "line_start": 10, "line_end": 20}]
        result = _filter_findings(findings, "/file.swift", {}, False)
        assert result == findings

    def test_list_ranges_overlap(self):
        findings = [{"id": "a", "line_start": 10, "line_end": 20}]
        lookup = {"/file.swift": [{"start": 15, "end": 25}]}
        result = _filter_findings(findings, "/file.swift", lookup, False)
        assert len(result) == 1

    def test_list_ranges_no_overlap(self):
        findings = [{"id": "a", "line_start": 10, "line_end": 20}]
        lookup = {"/file.swift": [{"start": 50, "end": 60}]}
        result = _filter_findings(findings, "/file.swift", lookup, False)
        assert len(result) == 0


# ---------- _match_suggestions ----------

class TestMatchSuggestions:
    def test_no_suggestions(self):
        findings = [{"id": "srp-001"}]
        result = _match_suggestions(findings, {})
        assert result == []

    def test_matching_suggestion(self):
        findings = [{"id": "srp-001"}]
        suggestions_by_finding = {
            "srp-001": [{"id": "srp-fix-001", "addresses": ["srp-001"]}]
        }
        result = _match_suggestions(findings, suggestions_by_finding)
        assert len(result) == 1
        assert result[0]["id"] == "srp-fix-001"

    def test_deduplication(self):
        findings = [{"id": "srp-001"}, {"id": "srp-002"}]
        shared_suggestion = {"id": "srp-fix-001", "addresses": ["srp-001", "srp-002"]}
        suggestions_by_finding = {
            "srp-001": [shared_suggestion],
            "srp-002": [shared_suggestion],
        }
        result = _match_suggestions(findings, suggestions_by_finding)
        assert len(result) == 1  # same suggestion, not duplicated

    def test_multiple_suggestions(self):
        findings = [{"id": "srp-001"}, {"id": "srp-002"}]
        suggestions_by_finding = {
            "srp-001": [{"id": "srp-fix-001", "addresses": ["srp-001"]}],
            "srp-002": [{"id": "srp-fix-002", "addresses": ["srp-002"]}],
        }
        result = _match_suggestions(findings, suggestions_by_finding)
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
    return {
        "agent": "srp",
        "principle": "Single Responsibility Principle",
        "timestamp": "2026-01-01T00:00:00Z",
        "files": [
            {
                "file_path": "/project/MyFile.swift",
                "units": [
                    {
                        "unit_name": "MyClass",
                        "unit_kind": "class",
                        "metrics": {
                            "verbs": {"count": 4, "table": [
                                {"method": "fetch", "verb": "fetches"},
                                {"method": "parse", "verb": "parses"},
                                {"method": "save", "verb": "saves"},
                                {"method": "notify", "verb": "notifies"},
                            ]},
                            "cohesion_groups": {
                                "count": 2,
                                "method_variable_table": [],
                                "groups": [
                                    {"name": "Data", "variables": ["db"], "methods": ["fetch", "save"]},
                                    {"name": "Notify", "variables": ["notifier"], "methods": ["parse", "notify"]},
                                ],
                            },
                            "stakeholders": {"count": 2, "table": [
                                {"verb": "fetches", "stakeholder": "Data Team"},
                                {"verb": "notifies", "stakeholder": "Ops"},
                            ]},
                            "cross_reference": [],
                        },
                        "scoring": {
                            "cohesion_severity": "SEVERE",
                            "verb_severity": "SEVERE",
                            "stakeholder_count": 2,
                            "final_severity": "SEVERE",
                        },
                        "findings": [
                            {
                                "id": "srp-001",
                                "severity": "SEVERE",
                                "metric": "SRP-2",
                                "title": "Multiple cohesion groups",
                                "issue": "2 cohesion groups found",
                                "line_start": 1,
                                "line_end": 50,
                            }
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

    def test_schema_validation_catches_invalid(self, tmp_path):
        """When plugin-root is provided, invalid JSON should fail."""
        prepare_dir = tmp_path / "prepare"
        prepare_dir.mkdir()
        rules_dir = tmp_path / "rules" / "srp"
        rules_dir.mkdir(parents=True)

        review_input = _build_review_input()
        (prepare_dir / "review-input.json").write_text(json.dumps(review_input))

        # Invalid: severity "CRITICAL" is not in the enum
        review_output = _build_review_output()
        review_output["files"][0]["units"][0]["scoring"]["final_severity"] = "CRITICAL"
        (rules_dir / "review-output.json").write_text(json.dumps(review_output))

        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(tmp_path), str(PLUGIN_ROOT)],
            capture_output=True, text=True,
        )
        assert result.returncode == 1
        assert "Schema validation failed" in result.stderr

    def test_no_plugin_root_skips_validation(self, tmp_path):
        """Without plugin-root, invalid JSON should still be processed."""
        prepare_dir = tmp_path / "prepare"
        prepare_dir.mkdir()
        rules_dir = tmp_path / "rules" / "srp"
        rules_dir.mkdir(parents=True)

        review_input = _build_review_input()
        (prepare_dir / "review-input.json").write_text(json.dumps(review_input))

        review_output = _build_review_output()
        review_output["files"][0]["units"][0]["scoring"]["final_severity"] = "CRITICAL"
        (rules_dir / "review-output.json").write_text(json.dumps(review_output))

        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(tmp_path)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0  # no validation = no failure
