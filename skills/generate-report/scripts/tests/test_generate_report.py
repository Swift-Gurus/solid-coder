"""Tests for generate-report.py"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from importlib import import_module

gr = import_module("generate-report")

badge_class = gr.badge_class
worst_severity = gr.worst_severity
render_code_blocks = gr.render_code_blocks
render_finding = gr.render_finding
render_suggestion = gr.render_suggestion
render_verification = gr.render_verification

SCRIPT = Path(__file__).resolve().parent.parent / "generate-report.py"


# ---------- badge_class ----------

class TestBadgeClass:
    def test_compliant(self):
        assert badge_class("COMPLIANT") == "badge-compliant"

    def test_minor(self):
        assert badge_class("MINOR") == "badge-minor"

    def test_severe(self):
        assert badge_class("SEVERE") == "badge-severe"


# ---------- worst_severity ----------

class TestWorstSeverity:
    def test_empty(self):
        assert worst_severity([]) == "COMPLIANT"

    def test_single(self):
        assert worst_severity(["MINOR"]) == "MINOR"

    def test_mixed(self):
        assert worst_severity(["COMPLIANT", "SEVERE", "MINOR"]) == "SEVERE"

    def test_all_compliant(self):
        assert worst_severity(["COMPLIANT", "COMPLIANT"]) == "COMPLIANT"


# ---------- render_code_blocks ----------

class TestRenderCodeBlocks:
    def test_single_code_fence(self):
        text = "```swift\nlet x = 1\n```"
        result = render_code_blocks(text)
        assert '<div class="code-block">' in result
        assert "let x = 1" in result

    def test_text_between_fences(self):
        text = "Some text\n\n```swift\ncode\n```\n\nMore text"
        result = render_code_blocks(text)
        assert "<p>Some text</p>" in result
        assert "<p>More text</p>" in result
        assert '<div class="code-block">' in result

    def test_empty_input(self):
        assert render_code_blocks("") == ""

    def test_html_escaping_in_code(self):
        text = "```swift\nlet x: Array<Int> = []\n```"
        result = render_code_blocks(text)
        assert "&lt;" in result  # < is escaped
        assert "&gt;" in result  # > is escaped


# ---------- render_finding ----------

class TestRenderFinding:
    def test_basic_structure(self):
        finding = {
            "id": "srp-001",
            "severity": "SEVERE",
            "metric": "SRP-2",
            "title": "Multiple cohesion groups",
            "issue": "2 groups found",
        }
        html = render_finding(finding)
        assert "finding-card" in html
        assert "severity-severe" in html
        assert "srp-001" in html
        assert "SRP-2" in html
        assert "Multiple cohesion groups" in html

    def test_with_lines(self):
        finding = {
            "id": "srp-001",
            "severity": "MINOR",
            "metric": "SRP-1",
            "title": "Test",
            "issue": "Test issue",
            "line_start": 10,
            "line_end": 20,
        }
        html = render_finding(finding)
        assert "10" in html
        assert "20" in html

    def test_with_impact(self):
        finding = {
            "id": "ocp-001",
            "severity": "SEVERE",
            "metric": "OCP-1",
            "title": "Sealed point",
            "issue": "Singleton",
            "impact": "Cannot test",
        }
        html = render_finding(finding)
        assert "Cannot test" in html

    def test_html_escaping(self):
        finding = {
            "id": "lsp-001",
            "severity": "SEVERE",
            "metric": "LSP-1",
            "title": "Type <check>",
            "issue": "Uses as? with <Type>",
        }
        html = render_finding(finding)
        assert "&lt;check&gt;" in html
        assert "&lt;Type&gt;" in html


# ---------- render_suggestion ----------

class TestRenderSuggestion:
    def test_basic_structure(self):
        suggestion = {
            "id": "srp-fix-001",
            "severity": "SEVERE",
            "title": "Extract concern",
            "addresses": ["srp-001", "srp-002"],
            "suggested_fix": "Extract DataFetcher class",
            "todo_items": ["Create protocol", "Move methods"],
        }
        html = render_suggestion(suggestion)
        assert "fix-card" in html
        assert "srp-fix-001" in html
        assert "<code>srp-001</code>" in html
        assert "<code>srp-002</code>" in html
        assert "Create protocol" in html
        assert "Move methods" in html

    def test_with_pattern(self):
        suggestion = {
            "id": "ocp-fix-001",
            "severity": "SEVERE",
            "title": "Inject dependency",
            "addresses": ["ocp-001"],
            "pattern": "dependency_injection",
            "suggested_fix": "Use protocol",
            "todo_items": [],
        }
        html = render_suggestion(suggestion)
        assert "dependency_injection" in html
        assert "pattern-tag" in html

    def test_with_verification(self):
        suggestion = {
            "id": "srp-fix-001",
            "severity": "SEVERE",
            "title": "Extract",
            "addresses": ["srp-001"],
            "suggested_fix": "Split class",
            "todo_items": [],
            "verification": {
                "original_class": {"expected_severity": "COMPLIANT"},
                "extracted_types": [{"name": "DataFetcher", "expected_severity": "COMPLIANT"}],
            },
        }
        html = render_suggestion(suggestion)
        assert "verification" in html
        assert "DataFetcher" in html


# ---------- render_verification ----------

class TestRenderVerification:
    def test_none(self):
        assert render_verification(None) == ""

    def test_empty_dict(self):
        assert render_verification({}) == ""

    def test_original_only(self):
        v = {"original_class": {"expected_severity": "COMPLIANT"}}
        html = render_verification(v)
        assert "Original" in html
        assert "COMPLIANT" in html

    def test_with_extracted_types(self):
        v = {
            "original_class": {"expected_severity": "COMPLIANT"},
            "extracted_types": [{"name": "Fetcher", "expected_severity": "COMPLIANT"}],
        }
        html = render_verification(v)
        assert "Fetcher" in html

    def test_with_refactored_types(self):
        v = {
            "original_class": {"expected_severity": "MINOR"},
            "refactored_types": [{"name": "Adapter", "expected_severity": "COMPLIANT"}],
        }
        html = render_verification(v)
        assert "Adapter" in html


# ---------- Integration ----------

MINIMAL_TEMPLATE = "<style>.badge{}</style>"


class TestIntegration:
    def test_end_to_end(self, tmp_path):
        """Build minimal by-file directory, run script, verify report.html."""
        by_file = tmp_path / "by-file"
        by_file.mkdir()

        output_data = {
            "file_path": "/project/MyFile.swift",
            "timestamp": "2026-01-01T00:00:00Z",
            "principles": [
                {
                    "agent": "srp",
                    "principle": "Single Responsibility Principle",
                    "severity": "SEVERE",
                    "findings": [
                        {
                            "id": "srp-001",
                            "severity": "SEVERE",
                            "metric": "SRP-2",
                            "title": "Multiple groups",
                            "issue": "2 cohesion groups",
                            "line_start": 1,
                            "line_end": 50,
                        }
                    ],
                    "suggestions": [],
                }
            ],
        }
        (by_file / "MyFile.swift.output.json").write_text(json.dumps(output_data))

        template_path = tmp_path / "template.html"
        template_path.write_text(MINIMAL_TEMPLATE)

        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(tmp_path), str(template_path)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

        report = tmp_path / "report.html"
        assert report.exists()
        html = report.read_text()
        assert "SOLID Code Review Report" in html
        assert "MyFile.swift" in html
        assert "srp-001" in html
        assert "SEVERE" in html
