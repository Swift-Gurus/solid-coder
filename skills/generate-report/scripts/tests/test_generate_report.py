"""Tests for generate-report.py"""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from importlib import import_module

gr = import_module("generate-report")

badge_class = gr.badge_class
worst_severity = gr.worst_severity
render_code_blocks = gr.render_code_blocks
render_finding = gr.render_finding
render_action = gr.render_action
md_finding = gr.md_finding
md_action = gr.md_action

SCRIPT = Path(__file__).resolve().parent.parent / "generate-report.py"


class TestBadgeClass:
    def test_compliant(self):
        assert badge_class("COMPLIANT") == "badge-compliant"

    def test_severe(self):
        assert badge_class("SEVERE") == "badge-severe"


class TestWorstSeverity:
    def test_empty(self):
        assert worst_severity([]) == "COMPLIANT"

    def test_mixed(self):
        assert worst_severity(["COMPLIANT", "SEVERE", "MINOR"]) == "SEVERE"


class TestRenderCodeBlocks:
    def test_single_code_fence(self):
        result = render_code_blocks("```swift\nlet x = 1\n```")
        assert '<pre class="code-block">' in result and "<code>" in result
        assert "let x = 1" in result

    def test_preserves_indentation(self):
        result = render_code_blocks("```swift\nclass Foo {\n    func bar() {}\n}\n```")
        assert "    func bar()" in result  # indent intact

    def test_unfenced_code_is_wrapped_as_pre(self):
        """Real agent output often has narrative labels between unfenced code blocks."""
        text = (
            "Before (lines 42-78):\n\n"
            "func givenHolder() async {\n"
            "    await assertDeallocationCancelsTasks { _ in }\n"
            "}\n\n"
            "After:\n\n"
            "func newTest() {}\n"
        )
        result = render_code_blocks(text)
        assert "<p>Before (lines 42-78):</p>" in result
        assert "<p>After:</p>" in result
        assert '<pre class="code-block">' in result
        assert "    await assertDeallocationCancelsTasks" in result  # indent preserved

    def test_html_escaping_in_code(self):
        result = render_code_blocks("```swift\nlet x: Array<Int> = []\n```")
        assert "&lt;" in result and "&gt;" in result


class TestRenderFinding:
    def test_basic_structure(self):
        html = render_finding({
            "id": "srp-001", "severity": "SEVERE", "metric": "SRP-2",
            "title": "Multiple cohesion groups", "issue": "2 groups found",
        })
        assert "finding-card" in html and "severity-severe" in html
        assert "srp-001" in html and "SRP-2" in html

    def test_html_escaping(self):
        html = render_finding({
            "id": "lsp-001", "severity": "SEVERE", "metric": "LSP-1",
            "title": "Type <check>", "issue": "Uses as? with <Type>",
        })
        assert "&lt;check&gt;" in html


class TestRenderAction:
    def test_basic_structure(self):
        html = render_action({
            "suggestion_id": "holistic-001", "principle": "SRP",
            "resolves": ["srp-001", "srp-002"],
            "todo_items": ["Create protocol", "Move methods"],
            "suggested_fix": "```swift\nprotocol Foo {}\n```",
        })
        assert "fix-card" in html and "holistic-001" in html
        assert "<code>srp-001</code>" in html
        assert "Create protocol" in html

    def test_cross_check_rendering(self):
        html = render_action({
            "suggestion_id": "a1", "principle": "OCP", "resolves": [],
            "todo_items": [], "suggested_fix": "",
            "cross_check_results": [
                {"principle": "SRP", "passed": True, "detail": "ok"},
                {"principle": "LSP", "passed": False, "detail": "fails"},
            ],
        })
        assert "SRP" in html and "LSP" in html


class TestMarkdown:
    def test_md_finding(self):
        md = md_finding({
            "id": "srp-001", "severity": "SEVERE", "metric": "SRP-2",
            "title": "Groups", "issue": "2 groups", "impact": "hard to test",
            "line_start": 1, "line_end": 10,
        })
        assert "`srp-001`" in md and "SEVERE" in md
        assert "hard to test" in md and "1–10" in md

    def test_md_action(self):
        md = md_action({
            "suggestion_id": "holistic-001", "principle": "SRP",
            "resolves": ["srp-001"], "todo_items": ["step 1"],
            "suggested_fix": "code here",
        })
        assert "holistic-001" in md and "srp-001" in md
        assert "- [ ] step 1" in md


class TestIntegration:
    def test_end_to_end_md_and_html(self, tmp_path):
        data_dir = tmp_path / "1"
        by_file = data_dir / "by-file"
        synth = data_dir / "synthesized"
        by_file.mkdir(parents=True)
        synth.mkdir(parents=True)

        (by_file / "MyFile.swift.output.json").write_text(json.dumps({
            "file_path": "/project/MyFile.swift",
            "timestamp": "2026-01-01T00:00:00Z",
            "principles": [{
                "agent": "srp", "principle": "Single Responsibility Principle",
                "severity": "SEVERE",
                "findings": [{
                    "id": "srp-001", "severity": "SEVERE", "metric": "SRP-2",
                    "title": "Multiple groups", "issue": "2 cohesion groups",
                    "line_start": 1, "line_end": 50,
                }],
                "suggestions": [],
            }],
        }))

        (synth / "MyFile.plan.json").write_text(json.dumps({
            "file_path": "/project/MyFile.swift",
            "timestamp": "2026-01-01T00:00:00Z",
            "actions": [{
                "suggestion_id": "holistic-001", "principle": "SRP",
                "resolves": ["srp-001"],
                "todo_items": ["Extract DataFetcher"],
                "suggested_fix": "```swift\nclass DataFetcher {}\n```",
            }],
            "unresolved": [],
            "conflicts_detected": [],
        }))

        report_dir = tmp_path
        template = tmp_path / "template.html"
        template.write_text("<style>.badge{}</style>")

        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(data_dir), str(report_dir),
             "--template", str(template)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

        html = (report_dir / "report.html").read_text()
        md = (report_dir / "report.md").read_text()

        assert "MyFile.swift" in html and "srp-001" in html
        assert "holistic-001" in html and "DataFetcher" in html

        assert "# SOLID Code Review Report" in md
        assert "MyFile.swift" in md and "`srp-001`" in md
        assert "holistic-001" in md
