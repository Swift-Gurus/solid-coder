"""Tests for code_health_check.py"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

HOOKS_DIR = str(Path(__file__).resolve().parents[1])
if HOOKS_DIR not in sys.path:
    sys.path.insert(0, HOOKS_DIR)

import code_health_check as hook

LONG_SWIFT = "import Foundation\n\nfinal class Foo {\n" + "    func bar() {}\n" * 35 + "}\n"
SWIFTUI_SWIFT = "import SwiftUI\n\nstruct FooView: View {\n" + "    var body: some View { Text(\"\") }\n" * 35 + "}\n"
SHORT_SWIFT = "final class Foo {\n    func bar() {}\n}\n"

VIOLATIONS = [
    {"principle": "SRP", "issue": "Two concerns.", "fix": "Extract one."},
    {"principle": "OCP", "issue": "Sealed point.", "fix": "Inject protocol."},
]


def _haiku_json(violations: list) -> MagicMock:
    payload = json.dumps({"violations": violations})
    m = MagicMock()
    m.returncode = 0
    m.stdout = json.dumps([{"type": "result", "result": payload}])
    return m


def _gateway_tags(tags: list) -> MagicMock:
    m = MagicMock()
    m.returncode = 0
    m.stdout = json.dumps({"candidate_tags": tags})
    return m


def _gateway_rules(paths: list) -> MagicMock:
    m = MagicMock()
    m.returncode = 0
    m.stdout = json.dumps({"paths_to_load": paths})
    return m


def _call_main(stdin_json: dict) -> tuple:
    import io
    from contextlib import redirect_stdout
    stdout_buf = io.StringIO()
    exit_code = 0
    with patch("sys.stdin", io.StringIO(json.dumps(stdin_json))):
        with redirect_stdout(stdout_buf):
            try:
                hook.main()
            except SystemExit as e:
                exit_code = e.code or 0
    return exit_code, stdout_buf.getvalue()


def _write_event(file_path: str, content: str) -> dict:
    return {
        "tool_name": "Write",
        "tool_input": {"file_path": file_path, "content": content},
        "session_id": "test-session",
    }


def _edit_event(file_path: str, new_string: str) -> dict:
    return {
        "tool_name": "Edit",
        "tool_input": {"file_path": file_path, "old_string": "old", "new_string": new_string},
        "session_id": "test-session",
    }


class TestParseViolations(unittest.TestCase):
    def test_parses_violation_list(self):
        raw = json.dumps({"violations": VIOLATIONS})
        result = hook._parse_violations(raw)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["principle"], "SRP")

    def test_returns_empty_list_when_clean(self):
        self.assertEqual(hook._parse_violations(json.dumps({"violations": []})), [])

    def test_handles_code_fences(self):
        raw = "```json\n" + json.dumps({"violations": VIOLATIONS}) + "\n```"
        self.assertEqual(len(hook._parse_violations(raw)), 2)

    def test_handles_surrounding_text(self):
        raw = "Here:\n" + json.dumps({"violations": VIOLATIONS}) + "\nDone."
        self.assertEqual(len(hook._parse_violations(raw)), 2)

    def test_filters_malformed_entries(self):
        raw = json.dumps({"violations": [{"principle": "SRP"}, VIOLATIONS[0]]})
        self.assertEqual(len(hook._parse_violations(raw)), 1)

    def test_returns_none_for_invalid_json(self):
        self.assertIsNone(hook._parse_violations("not json"))

    def test_returns_none_when_violations_not_list(self):
        self.assertIsNone(hook._parse_violations(json.dumps({"violations": "bad"})))


class TestFormatBlockReason(unittest.TestCase):
    def test_includes_count(self):
        self.assertIn("2 violation(s)", hook._format_block_reason(VIOLATIONS))

    def test_includes_each_principle(self):
        reason = hook._format_block_reason(VIOLATIONS)
        self.assertIn("SRP", reason)
        self.assertIn("OCP", reason)

    def test_includes_issue_and_fix(self):
        reason = hook._format_block_reason(VIOLATIONS)
        self.assertIn("Two concerns.", reason)
        self.assertIn("Extract one.", reason)


class TestDetectTags(unittest.TestCase):
    def test_detects_swiftui_from_import(self):
        self.assertIn("swiftui", hook._detect_tags("import SwiftUI", ["swiftui"]))

    def test_detects_structured_concurrency_from_async(self):
        self.assertIn("structured-concurrency", hook._detect_tags("async func foo()", ["structured-concurrency"]))

    def test_no_match_returns_empty(self):
        self.assertEqual(hook._detect_tags("final class Foo {}", ["swiftui"]), [])

    def test_ui_test_excludes_unit_test_and_xctest(self):
        # UITest file matches xctest (import XCTest) AND ui-test (XCUIApplication)
        content = "import XCTest\nlet app = XCUIApplication()"
        tags = ["unit-test", "xctest", "ui-test"]
        matched = hook._detect_tags(content, tags)
        self.assertIn("ui-test", matched)
        self.assertNotIn("xctest", matched)
        self.assertNotIn("unit-test", matched)

    def test_unit_test_excludes_ui_test(self):
        content = "import Testing\n@Test func testFoo() {}"
        tags = ["unit-test", "xctest", "ui-test"]
        matched = hook._detect_tags(content, tags)
        self.assertIn("unit-test", matched)
        self.assertNotIn("ui-test", matched)

    def test_xctest_without_xcuiapplication_excludes_ui_test(self):
        content = "import XCTest\nclass FooTests: XCTestCase {}"
        tags = ["xctest", "ui-test"]
        matched = hook._detect_tags(content, tags)
        self.assertIn("xctest", matched)
        self.assertNotIn("ui-test", matched)


class TestPrincipleDisplayName(unittest.TestCase):
    def test_reads_displayName_from_rule_md(self):
        with tempfile.TemporaryDirectory() as d:
            principle_dir = Path(d) / "principle_dir"
            code_dir = principle_dir / "code"
            code_dir.mkdir(parents=True)
            (principle_dir / "rule.md").write_text(
                "---\nname: unit-testing\ndisplayName: Unit Testing\n---\nContent.\n"
            )
            instructions = code_dir / "instructions.md"
            instructions.write_text("Instructions.")
            self.assertEqual(hook._principle_display_name(instructions), "Unit Testing")

    def test_falls_back_to_folder_name_when_no_rule_md(self):
        with tempfile.TemporaryDirectory() as d:
            principle_dir = Path(d) / "SRP"
            code_dir = principle_dir / "code"
            code_dir.mkdir(parents=True)
            instructions = code_dir / "instructions.md"
            instructions.write_text("Instructions.")
            self.assertEqual(hook._principle_display_name(instructions), "SRP")

    def test_falls_back_to_folder_name_when_displayName_absent(self):
        with tempfile.TemporaryDirectory() as d:
            principle_dir = Path(d) / "MyPrinciple"
            code_dir = principle_dir / "code"
            code_dir.mkdir(parents=True)
            (principle_dir / "rule.md").write_text("---\nname: my-principle\n---\nNo displayName here.\n")
            instructions = code_dir / "instructions.md"
            instructions.write_text("Instructions.")
            self.assertEqual(hook._principle_display_name(instructions), "MyPrinciple")

    def test_loads_rules_uses_displayName_as_section_header(self):
        with tempfile.TemporaryDirectory() as d:
            principle_dir = Path(d) / "swift"
            code_dir = principle_dir / "code"
            code_dir.mkdir(parents=True)
            (principle_dir / "rule.md").write_text(
                "---\ndisplayName: Unit Testing\n---\n"
            )
            instructions = code_dir / "instructions.md"
            instructions.write_text("Rule body.")
            with patch("code_health_check.subprocess.run",
                       return_value=_gateway_rules([str(instructions)])):
                result = hook._load_rules([])
        self.assertIn("## Unit Testing", result)
        self.assertNotIn("## swift", result)


class TestLoadRules(unittest.TestCase):
    def test_passes_matched_tags_to_gateway(self):
        captured = []

        def side_effect(cmd, **kwargs):
            captured.append(cmd)
            return _gateway_rules([])

        with patch("code_health_check.subprocess.run", side_effect=side_effect):
            hook._load_rules(["swiftui"])

        cmd = captured[0]
        self.assertIn("--matched_tags", cmd)
        self.assertIn("swiftui", cmd[cmd.index("--matched_tags") + 1])

    def test_reads_and_strips_frontmatter(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("---\nname: test\n---\n\nRule content.\n")
            tmp = f.name
        try:
            with patch("code_health_check.subprocess.run", return_value=_gateway_rules([tmp])):
                result = hook._load_rules([])
            self.assertIn("Rule content.", result)
            self.assertNotIn("---", result)
        finally:
            os.unlink(tmp)

    def test_returns_none_on_gateway_failure(self):
        m = MagicMock()
        m.returncode = 1
        with patch("code_health_check.subprocess.run", return_value=m):
            self.assertIsNone(hook._load_rules([]))

    def test_returns_none_for_empty_paths(self):
        with patch("code_health_check.subprocess.run", return_value=_gateway_rules([])):
            self.assertIsNone(hook._load_rules([]))


class TestCheck(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
        self._tmp.write("Rule content.")
        self._tmp.close()

    def tearDown(self):
        os.unlink(self._tmp.name)

    def _pipeline(self, violations):
        seq = [_gateway_tags([]), _gateway_rules([self._tmp.name]), _haiku_json(violations)]
        it = iter(seq)
        return lambda *a, **kw: next(it)

    def test_returns_violations_list(self):
        with patch("code_health_check.subprocess.run", side_effect=self._pipeline(VIOLATIONS)):
            result = hook._check(LONG_SWIFT, "/src/Foo.swift", "Swift", "")
        self.assertEqual(len(result), 2)

    def test_returns_empty_list_when_clean(self):
        with patch("code_health_check.subprocess.run", side_effect=self._pipeline([])):
            self.assertEqual(hook._check(LONG_SWIFT, "/src/Foo.swift", "Swift", ""), [])

    def test_returns_none_on_gateway_failure(self):
        m = MagicMock()
        m.returncode = 1
        with patch("code_health_check.subprocess.run", return_value=m):
            self.assertIsNone(hook._check(LONG_SWIFT, "/src/Foo.swift", "Swift", ""))

    def test_returns_none_on_timeout(self):
        seq = [_gateway_tags([]), _gateway_rules([self._tmp.name])]
        timeout_mock = MagicMock(side_effect=subprocess.TimeoutExpired("claude", 300))
        seq.append(timeout_mock)
        it = iter(seq)
        with patch("code_health_check.subprocess.run", side_effect=lambda *a, **kw: next(it)):
            self.assertIsNone(hook._check(LONG_SWIFT, "/src/Foo.swift", "Swift", ""))


class TestMainHook(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
        self._tmp.write("Rule content.")
        self._tmp.close()

    def tearDown(self):
        os.unlink(self._tmp.name)

    def _pipeline(self, violations):
        seq = [_gateway_tags([]), _gateway_rules([self._tmp.name]), _haiku_json(violations)]
        it = iter(seq)
        return lambda *a, **kw: next(it)

    def test_unsupported_extension_allows_without_gateway(self):
        with patch("code_health_check.subprocess.run") as mock_run:
            code, out = _call_main(_write_event("/src/Foo.py", LONG_SWIFT))
        mock_run.assert_not_called()
        self.assertEqual(code, 0)

    def test_test_file_allows_without_gateway(self):
        with patch("code_health_check.subprocess.run") as mock_run:
            code, out = _call_main(_write_event("/src/FooTests.swift", LONG_SWIFT))
        mock_run.assert_not_called()
        self.assertEqual(code, 0)

    def test_short_file_runs_health_check(self):
        """Health check always runs for .swift files regardless of size."""
        with patch("code_health_check.subprocess.run",
                   side_effect=self._pipeline([])) as mock_run:
            code, out = _call_main(_write_event("/src/Foo.swift", SHORT_SWIFT))
        self.assertGreater(mock_run.call_count, 0)
        self.assertEqual(code, 0)

    def test_clean_file_allows(self):
        with patch("code_health_check.subprocess.run", side_effect=self._pipeline([])):
            code, out = _call_main(_write_event("/src/Foo.swift", LONG_SWIFT))
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_violations_block_with_structured_reason(self):
        with patch("code_health_check.subprocess.run", side_effect=self._pipeline(VIOLATIONS)):
            code, out = _call_main(_write_event("/src/Foo.swift", LONG_SWIFT))
        payload = json.loads(out)
        h = payload["hookSpecificOutput"]
        self.assertEqual(h["permissionDecision"], "deny")
        self.assertIn("2 violation(s)", h["permissionDecisionReason"])
        self.assertIn("SRP", h["permissionDecisionReason"])

    def test_edit_tool_is_checked(self):
        with patch("code_health_check.subprocess.run", side_effect=self._pipeline(VIOLATIONS)):
            code, out = _call_main(_edit_event("/src/Foo.swift", LONG_SWIFT))
        payload = json.loads(out)
        self.assertEqual(payload["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_gateway_failure_fails_open(self):
        m = MagicMock()
        m.returncode = 1
        with patch("code_health_check.subprocess.run", return_value=m):
            code, out = _call_main(_write_event("/src/Foo.swift", LONG_SWIFT))
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_malformed_stdin_allows(self):
        import io
        with patch("sys.stdin", io.StringIO("not json")):
            try:
                hook.main()
            except SystemExit as e:
                self.assertEqual(e.code or 0, 0)


if __name__ == "__main__":
    unittest.main()
