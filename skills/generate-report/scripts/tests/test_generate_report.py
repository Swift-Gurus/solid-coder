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
md_violation = gr.md_violation
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
        assert "    func bar()" in result

    def test_unfenced_code_is_wrapped_as_pre(self):
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
        assert "    await assertDeallocationCancelsTasks" in result

    def test_html_escaping_in_code(self):
        result = render_code_blocks("```swift\nlet x: Array<Int> = []\n```")
        assert "&lt;" in result and "&gt;" in result


class TestRenderFinding:
    def test_basic_structure(self):
        html = render_finding({"rule_id": "SRP-2", "severity": "SEVERE"})
        assert "finding-card" in html and "severity-severe" in html
        assert "SRP-2" in html

    def test_minor_severity(self):
        html = render_finding({"rule_id": "OCP-1", "severity": "MINOR"})
        assert "severity-minor" in html and "OCP-1" in html


class TestRenderAction:
    def test_basic_structure(self):
        html = render_action({
            "suggestion_id": "holistic-001", "principle": "SRP",
            "resolves": ["SRP-1", "SRP-2"],
            "todo_items": ["Create protocol", "Move methods"],
            "suggested_fix": "```swift\nprotocol Foo {}\n```",
        })
        assert "fix-card" in html and "holistic-001" in html
        assert "<code>SRP-1</code>" in html
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
    def test_md_violation(self):
        md = md_violation({"rule_id": "SRP-2", "severity": "SEVERE"})
        assert "SRP-2" in md and "SEVERE" in md

    def test_md_action(self):
        md = md_action({
            "suggestion_id": "holistic-001", "principle": "SRP",
            "resolves": ["SRP-1"], "todo_items": ["step 1"],
            "suggested_fix": "code here",
        })
        assert "holistic-001" in md and "SRP-1" in md
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
                "principle": "SRP",
                "severity": "SEVERE",
                "violations": [{"rule_id": "SRP-2", "severity": "SEVERE"}],
                "suggestions": [],
            }],
        }))

        (synth / "MyFile.plan.json").write_text(json.dumps({
            "file_path": "/project/MyFile.swift",
            "timestamp": "2026-01-01T00:00:00Z",
            "actions": [{
                "suggestion_id": "holistic-001", "principle": "SRP",
                "resolves": ["SRP-2"],
                "todo_items": ["Extract DataFetcher"],
                "suggested_fix": "```swift\nclass DataFetcher {}\n```",
            }],
            "unresolved": [],
            "conflicts_detected": [],
        }))

        report_dir = tmp_path
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(tmp_path), str(report_dir)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert (report_dir / "report.md").exists()
        assert (report_dir / "report.html").exists()
        md = (report_dir / "report.md").read_text()
        assert "SRP-2" in md
