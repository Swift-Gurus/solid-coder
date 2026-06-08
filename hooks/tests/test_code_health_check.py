"""
solid-description: Verifies that code quality violations are accurately detected and reported.
solid-category: unit-test
"""

import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

import code_health_check as hook
import test_utils
from test_utils import make_subprocess_mock
from hc_violation_parser import ViolationParser, ScoredResultConverter
from hc_tag_detector import TagDetector
from hc_rule_loader import GatewayRuleLoader
from hc_checker import (
    HealthPromptBuilder, PrinciplesLoader, LLMReviewer,
    LLMExecutor, TextBasedOutputHandler, ResponseParser,
)

LONG_SWIFT = test_utils.LONG_SWIFT
SHORT_SWIFT = test_utils.SHORT_SWIFT

VIOLATIONS = [
    {"principle": "SRP", "issue": "Two concerns.", "fix": "Extract one.", "metric_id": "SRP-2"},
    {"principle": "OCP", "issue": "Sealed point.", "fix": "Inject protocol.", "metric_id": "OCP-1"},
]


def _gateway_tags(tags: list) -> MagicMock:
    return make_subprocess_mock(0, {"candidate_tags": tags})


def _gateway_detection_rules(principles: list) -> MagicMock:
    return make_subprocess_mock(0, {"principles": principles})


def _make_runner_mock(returncode: int, stdout_obj) -> MagicMock:
    m = MagicMock()
    m.run_cmd.return_value = stdout_obj if returncode == 0 else None
    return m


class TestViolationParser(unittest.TestCase):
    def setUp(self):
        self.parser = ViolationParser()

    def test_parses_violation_list(self):
        raw = json.dumps({"violations": VIOLATIONS})
        result = self.parser.parse(raw)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["principle"], "SRP")

    def test_returns_empty_list_when_clean(self):
        self.assertEqual(self.parser.parse(json.dumps({"violations": []})), [])

    def test_handles_code_fences(self):
        raw = "\n" + json.dumps({"violations": VIOLATIONS}) + "\n"
        self.assertEqual(len(self.parser.parse(raw)), 2)

    def test_handles_surrounding_text(self):
        raw = "Here:\n" + json.dumps({"violations": VIOLATIONS}) + "\nDone."
        self.assertEqual(len(self.parser.parse(raw)), 2)

    def test_filters_malformed_entries(self):
        raw = json.dumps({"violations": [{"principle": "SRP"}, VIOLATIONS[0]]})
        self.assertEqual(len(self.parser.parse(raw)), 1)

    def test_returns_none_for_invalid_json(self):
        self.assertIsNone(self.parser.parse("not json"))

    def test_returns_none_when_violations_not_list(self):
        self.assertIsNone(self.parser.parse(json.dumps({"violations": "bad"})))

    def test_format_block_reason_includes_count(self):
        self.assertIn("2 SEVERE violation(s)", self.parser.format_block_reason(VIOLATIONS))

    def test_format_block_reason_includes_each_principle(self):
        reason = self.parser.format_block_reason(VIOLATIONS)
        self.assertIn("SRP", reason)
        self.assertIn("OCP", reason)

    def test_format_block_reason_includes_issue(self):
        reason = self.parser.format_block_reason(VIOLATIONS)
        self.assertIn("Two concerns.", reason)


class TestScoredResultConverter(unittest.TestCase):
    def setUp(self):
        self.converter = ScoredResultConverter()

    def _make_entry(self, principle, unit_name, rule_id, severity):
        return {
            "files": [{"units": [{"unit_name": unit_name, "violations": [{"rule_id": rule_id, "severity": severity}]}]}],
        }

    def test_returns_empty_list_for_empty_input(self):
        self.assertEqual(self.converter.violations_from_scored([]), [])

    def test_skips_entries_with_error_key(self):
        result = self.converter.violations_from_scored([{"error": "timeout"}])
        self.assertEqual(result, [])

    def test_converts_severe_finding_to_violation(self):
        entry = self._make_entry("SRP", "UserManager", "SRP-1", "SEVERE")
        result = self.converter.violations_from_scored([entry])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["principle"], "SRP")
        self.assertEqual(result[0]["metric_id"], "SRP-1")

    def test_converts_minor_finding_to_violation(self):
        entry = self._make_entry("OCP", "Loader", "OCP-1", "MINOR")
        result = self.converter.violations_from_scored([entry])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["principle"], "OCP")

    def test_skips_compliant_findings(self):
        entry = self._make_entry("SRP", "CleanType", "SRP-1", "COMPLIANT")
        result = self.converter.violations_from_scored([entry])
        self.assertEqual(result, [])

    def test_aggregates_findings_across_multiple_entries(self):
        entries = [
            self._make_entry("SRP", "TypeA", "SRP-1", "SEVERE"),
            self._make_entry("OCP", "TypeB", "OCP-1", "MINOR"),
        ]
        result = self.converter.violations_from_scored(entries)
        self.assertEqual(len(result), 2)
        principles = {v["principle"] for v in result}
        self.assertIn("SRP", principles)
        self.assertIn("OCP", principles)

    def test_violation_issue_contains_metric_id_and_severity_and_unit(self):
        entry = self._make_entry("LSP", "MyStore", "LSP-3", "SEVERE")
        result = self.converter.violations_from_scored([entry])
        self.assertIn("LSP-3", result[0]["issue"])
        self.assertIn("SEVERE", result[0]["issue"])
        self.assertIn("MyStore", result[0]["issue"])

    def test_principle_derived_from_rule_id_prefix(self):
        entry = {
            "files": [{"units": [{"unit_name": "X", "violations": [{"rule_id": "DRY-1", "severity": "SEVERE"}]}]}],
        }
        result = self.converter.violations_from_scored([entry])
        self.assertEqual(result[0]["principle"], "DRY")


class TestTagDetector(unittest.TestCase):
    def setUp(self):
        self.detector = TagDetector()

    def test_detects_swiftui_from_import(self):
        self.assertIn("swiftui", self.detector.detect("import SwiftUI", ["swiftui"]))

    def test_detects_swiftui_from_view_conformance(self):
        self.assertIn("swiftui", self.detector.detect("struct Foo: View {", ["swiftui"]))

    def test_detects_swiftui_from_some_view(self):
        self.assertIn("swiftui", self.detector.detect("var body: some View {", ["swiftui"]))

    def test_does_not_false_positive_swiftui_from_uitableview(self):
        self.assertNotIn("swiftui", self.detector.detect("let v: UITableView", ["swiftui"]))

    def test_does_not_false_positive_swiftui_from_plain_view_word(self):
        self.assertNotIn("swiftui", self.detector.detect("func reviewData() {}", ["swiftui"]))

    def test_detects_structured_concurrency_from_async(self):
        self.assertIn(
            "structured-concurrency",
            self.detector.detect("async func foo()", ["structured-concurrency"]),
        )

    def test_detects_structured_concurrency_from_task_literal(self):
        self.assertIn(
            "structured-concurrency",
            self.detector.detect("Task { await fetch() }", ["structured-concurrency"]),
        )

    def test_does_not_false_positive_sc_from_urlsession_datatask(self):
        content = "let task = session.dataTask(with: url) { data, _, _ in }"
        self.assertNotIn("structured-concurrency", self.detector.detect(content, ["structured-concurrency"]))

    def test_detects_structured_concurrency_from_actor_declaration(self):
        self.assertIn(
            "structured-concurrency",
            self.detector.detect("actor MyService {", ["structured-concurrency"]),
        )

    def test_no_match_returns_empty(self):
        self.assertEqual(self.detector.detect("final class Foo {}", ["swiftui"]), [])

    def test_ui_test_excludes_unit_test_and_xctest(self):
        content = "import XCTest\nlet app = XCUIApplication()"
        matched = self.detector.detect(content, ["unit-test", "xctest", "ui-test"])
        self.assertIn("ui-test", matched)
        self.assertNotIn("xctest", matched)
        self.assertNotIn("unit-test", matched)

    def test_unit_test_excludes_ui_test(self):
        matched = self.detector.detect(
            "import Testing\n@Test func testFoo() {}",
            ["unit-test", "xctest", "ui-test"],
        )
        self.assertIn("unit-test", matched)
        self.assertNotIn("ui-test", matched)

    def test_xctest_without_xcuiapplication_excludes_ui_test(self):
        matched = self.detector.detect(
            "import XCTest\nclass FooTests: XCTestCase {}",
            ["xctest", "ui-test"],
        )
        self.assertIn("xctest", matched)
        self.assertNotIn("ui-test", matched)


class TestGatewayRuleLoader(unittest.TestCase):
    def _make_invoker(self, return_value=None):
        m = MagicMock()
        m.invoke.return_value = return_value
        return m

    def test_get_candidate_tags_returns_tag_list(self):
        loader = GatewayRuleLoader(invoker=self._make_invoker(["swiftui"]))
        self.assertEqual(loader.get_candidate_tags(), ["swiftui"])

    def test_get_candidate_tags_returns_empty_when_invoker_returns_empty(self):
        # GatewayInvoker returns its default=[] on runner failure;
        # GatewayRuleLoader just passes that through.
        loader = GatewayRuleLoader(invoker=self._make_invoker([]))
        self.assertEqual(loader.get_candidate_tags(), [])

    def test_load_detection_rules_returns_principles_dict(self):
        data = {"principles": [{"name": "srp"}]}
        loader = GatewayRuleLoader(invoker=self._make_invoker(data))
        self.assertIn("principles", loader.load_detection_rules(["swiftui"]))

    def test_load_detection_rules_returns_filtered_result(self):
        data = {"principles": [{"name": "swiftui", "content": "SwiftUI rules"}]}
        loader = GatewayRuleLoader(invoker=self._make_invoker(data))
        result = loader.load_detection_rules(["swiftui"])
        self.assertEqual(result["principles"][0]["name"], "swiftui")

    def test_load_detection_rules_returns_none_on_invoker_failure(self):
        loader = GatewayRuleLoader(invoker=self._make_invoker(None))
        self.assertIsNone(loader.load_detection_rules([]))


class TestPrinciplesLoader(unittest.TestCase):
    def _make_rules_mock(self, tags=None, rules_data=None):
        m = MagicMock()
        m.get_candidate_tags.return_value = tags or []
        m.load_detection_rules.return_value = rules_data
        return m

    def _make_tags_mock(self, matched=None):
        m = MagicMock()
        m.detect.return_value = matched or []
        return m

    def test_returns_principles_list_when_rules_load_succeeds(self):
        rules = self._make_rules_mock(rules_data={"principles": [{"name": "srp", "content": "..."}]})
        tags = self._make_tags_mock()
        loader = PrinciplesLoader(rules=rules, tags=tags)
        result = loader.load("code", "/src/Foo.swift")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "srp")

    def test_returns_none_when_rules_load_fails(self):
        rules = self._make_rules_mock(rules_data=None)
        tags = self._make_tags_mock()
        loader = PrinciplesLoader(rules=rules, tags=tags)
        self.assertIsNone(loader.load("code", "/src/Foo.swift"))

    def test_returns_empty_list_when_no_principles_active(self):
        rules = self._make_rules_mock(rules_data={"principles": []})
        tags = self._make_tags_mock()
        loader = PrinciplesLoader(rules=rules, tags=tags)
        self.assertEqual(loader.load("code", "/src/Foo.swift"), [])

    def test_passes_detected_tags_to_rules_loader(self):
        rules = self._make_rules_mock(rules_data={"principles": []})
        tags = self._make_tags_mock(matched=["swiftui"])
        loader = PrinciplesLoader(rules=rules, tags=tags)
        loader.load("import SwiftUI", "/src/Foo.swift")
        rules.load_detection_rules.assert_called_once_with(["swiftui"])


class TestLLMReviewer(unittest.TestCase):
    def _make_reviewer(self, runner_result=None, runner_raises=None, parse_result=None):
        runner = MagicMock()
        if runner_raises:
            runner.run.side_effect = runner_raises
        else:
            runner.run.return_value = runner_result
        logger = MagicMock()
        parser = MagicMock()
        parser.parse.return_value = parse_result
        reviewer = LLMReviewer(
            executor=LLMExecutor(runner=runner, logger=logger),
            output_handler=TextBasedOutputHandler(ResponseParser(parser=parser, logger=logger)),
        )
        return reviewer, logger

    def test_returns_violations_when_runner_and_parser_succeed(self):
        reviewer, _ = self._make_reviewer(
            runner_result='{"violations": []}',
            parse_result=[],
        )
        result = reviewer.review("prompt", "/src/Foo.swift")
        self.assertEqual(result, [])

    def test_raises_and_logs_when_runner_returns_empty(self):
        reviewer, logger = self._make_reviewer(runner_result=None)
        with self.assertRaises(RuntimeError):
            reviewer.review("prompt", "/src/Foo.swift")
        logger.log.assert_called_once()

    def test_raises_and_logs_when_runner_raises(self):
        reviewer, logger = self._make_reviewer(runner_raises=RuntimeError("timeout"))
        with self.assertRaises(RuntimeError):
            reviewer.review("prompt", "/src/Foo.swift")
        logger.log.assert_called_once()

    def test_returns_none_and_logs_when_parser_returns_none(self):
        reviewer, logger = self._make_reviewer(runner_result='bad json', parse_result=None)
        result = reviewer.review("prompt", "/src/Foo.swift")
        self.assertIsNone(result)
        logger.log.assert_called_once()


class TestHealthPromptBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = HealthPromptBuilder()

    def test_detection_instructions_appear_in_prompt(self):
        principles = [{"name": "srp", "content": "srp detection rules"}]
        prompt = self.builder.build(principles, "code here", "/src/Foo.swift", "")
        self.assertIn("srp detection rules", prompt)

    def test_detection_instructions_empty_when_no_content_key(self):
        # Principles that only carry full_content (old fallback shape) are skipped.
        principles = [{"name": "srp", "full_content": "srp detection rules"}]
        prompt = self.builder.build(principles, "code here", "/src/Foo.swift", "")
        self.assertNotIn("srp detection rules", prompt)

    def test_session_id_header_present_when_provided(self):
        prompt = self.builder.build([], "code", "/src/Foo.swift", "session-abc")
        self.assertTrue(prompt.startswith("# spawned-by: session-abc\n"))

    def test_session_id_header_absent_when_empty(self):
        prompt = self.builder.build([], "code", "/src/Foo.swift", "")
        self.assertNotIn("spawned-by", prompt)


class TestCheck(unittest.TestCase):
    """Tests for the full _check pipeline, always using the Claude backend.

    The gate now uses FileBasedOutputHandler — the LLM calls submit_batch_findings
    which writes scored files, then the reviewer reads them. Tests mock
    FileOutputReader.read_violations to inject pre-computed violation lists.
    """

    def _make_pipeline(self):
        tags_mock = _gateway_tags([])
        detection_mock = _gateway_detection_rules([{"name": "srp", "content": "rules",
                                                    "principle_name": "SRP", "metrics_example": {}}])
        claude_mock = make_subprocess_mock(0, [{"type": "result", "result": ""}])
        seq = [tags_mock, detection_mock, claude_mock]
        it = iter(seq)
        return lambda *a, **kw: next(it)

    def _claude_backend(self):
        """Force the Claude backend regardless of local config file."""
        return patch("hc_runner_factory.llm_backend", return_value="claude")

    def test_returns_violations_list_when_gateway_reports_findings(self):
        """Gate reads violations from submitted files (FileOutputReader), not LLM text."""
        mock_violations = [
            {"principle": "SRP", "metric_id": "SRP-2",
             "issue": "SRP-2: /src/Foo.swift, unit Foo — cohesion_groups >= 2 (measured: cohesion_groups=2)\n    -> Call mcp__docs__load_fix_for_violation(SRP-2) for fix guidance",
             "fix": "Call mcp__docs__load_fix_for_violation(SRP-2) for guidance."},
            {"principle": "OCP", "metric_id": "OCP-1",
             "issue": "OCP-1: /src/Foo.swift, unit Foo — sealed_variation_points >= 1 (measured: sealed_variation_points=2)\n    -> Call mcp__docs__load_fix_for_violation(OCP-1) for fix guidance",
             "fix": "Call mcp__docs__load_fix_for_violation(OCP-1) for guidance."},
        ]
        with self._claude_backend(), \
             patch("hook_utils.subprocess.run", side_effect=self._make_pipeline()), \
             patch("hc_checker.FileOutputReader.read_violations", return_value=mock_violations):
            result = hook._check(LONG_SWIFT, "/src/Foo.swift", "Swift", "test-session")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["principle"], "SRP")

    def test_returns_empty_list_when_no_findings(self):
        """No SEVERE violations → empty list."""
        with self._claude_backend(), \
             patch("hook_utils.subprocess.run", side_effect=self._make_pipeline()), \
             patch("hc_checker.FileOutputReader.read_violations", return_value=[]):
            result = hook._check(LONG_SWIFT, "/src/Foo.swift", "Swift", "test-session")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_raises_on_gateway_failure(self):
        from hook_utils import SubprocessError
        with self._claude_backend(), \
             patch("hook_utils.subprocess.run", return_value=make_subprocess_mock(1, {})):
            with self.assertRaises(SubprocessError):
                hook._check(LONG_SWIFT, "/src/Foo.swift", "Swift", "test-session")


class TestSupportedExtensions(unittest.TestCase):
    def test_py_extension_maps_to_python(self):
        self.assertEqual(hook.SUPPORTED_EXTENSIONS.get(".py"), "Python")

    def test_js_extension_absent(self):
        self.assertIsNone(hook.SUPPORTED_EXTENSIONS.get(".js"))

    def test_swift_extension_maps_to_swift(self):
        self.assertEqual(hook.SUPPORTED_EXTENSIONS.get(".swift"), "Swift")


if __name__ == "__main__":
    unittest.main()
