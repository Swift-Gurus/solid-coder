"""
solid-description: Verifies that code quality violations are accurately detected and reported.
solid-category: unit-test
"""

import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks", Path(__file__).resolve().parent)

import code_health_check as hook
import test_utils
from test_utils import make_subprocess_mock
from hc_violation_parser import ViolationParser
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


def _make_rule_loader_invoker(return_value=None) -> MagicMock:
    m = MagicMock()
    m.invoke.return_value = return_value
    return m


def _make_rules_mock(tags=None, rules_data=None) -> MagicMock:
    m = MagicMock()
    m.get_candidate_tags.return_value = tags or []
    m.load_detection_rules.return_value = rules_data
    return m


def _make_tags_mock(matched=None) -> MagicMock:
    m = MagicMock()
    m.detect.return_value = matched or []
    return m


def _make_reviewer(runner_result=None, runner_raises=None, parse_result=None):
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


def _make_check_pipeline():
    tags_mock = _gateway_tags([])
    detection_mock = _gateway_detection_rules([{"name": "srp", "content": "rules",
                                                "principle_name": "SRP", "metrics_example": {}}])
    output_path_mock = make_subprocess_mock(0, {"output_root": "/tmp/gate/test-session"})
    claude_mock = make_subprocess_mock(0, [{"type": "result", "result": ""}])
    seq = [tags_mock, detection_mock, output_path_mock, claude_mock]
    it = iter(seq)
    return lambda *a, **kw: next(it)


def _claude_backend_patch():
    from llm_config import LlmConfig
    from solid_coder_config import SolidCoderConfig
    return patch("hc_config.load_config", return_value=SolidCoderConfig(llm=LlmConfig(backend="claude")))


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
    def test_get_candidate_tags_returns_tag_list(self):
        loader = GatewayRuleLoader(invoker=_make_rule_loader_invoker(["swiftui"]))
        self.assertEqual(loader.get_candidate_tags(), ["swiftui"])

    def test_get_candidate_tags_returns_empty_when_invoker_returns_empty(self):
        loader = GatewayRuleLoader(invoker=_make_rule_loader_invoker([]))
        self.assertEqual(loader.get_candidate_tags(), [])

    def test_load_detection_rules_returns_principles_dict(self):
        data = {"principles": [{"name": "srp"}]}
        loader = GatewayRuleLoader(invoker=_make_rule_loader_invoker(data))
        self.assertIn("principles", loader.load_detection_rules(["swiftui"]))

    def test_load_detection_rules_returns_filtered_result(self):
        data = {"principles": [{"name": "swiftui", "content": "SwiftUI rules"}]}
        loader = GatewayRuleLoader(invoker=_make_rule_loader_invoker(data))
        result = loader.load_detection_rules(["swiftui"])
        self.assertEqual(result["principles"][0]["name"], "swiftui")

    def test_load_detection_rules_returns_none_on_invoker_failure(self):
        loader = GatewayRuleLoader(invoker=_make_rule_loader_invoker(None))
        self.assertIsNone(loader.load_detection_rules([]))


class TestPrinciplesLoader(unittest.TestCase):
    def test_returns_principles_list_when_rules_load_succeeds(self):
        rules = _make_rules_mock(rules_data={"principles": [{"name": "srp", "content": "..."}]})
        loader = PrinciplesLoader(rules=rules, tags=_make_tags_mock())
        result = loader.load("code", "/src/Foo.swift")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "srp")

    def test_returns_none_when_rules_load_fails(self):
        loader = PrinciplesLoader(rules=_make_rules_mock(rules_data=None), tags=_make_tags_mock())
        self.assertIsNone(loader.load("code", "/src/Foo.swift"))

    def test_returns_empty_list_when_no_principles_active(self):
        loader = PrinciplesLoader(rules=_make_rules_mock(rules_data={"principles": []}), tags=_make_tags_mock())
        self.assertEqual(loader.load("code", "/src/Foo.swift"), [])

    def test_passes_detected_tags_to_rules_loader(self):
        rules = _make_rules_mock(rules_data={"principles": []})
        loader = PrinciplesLoader(rules=rules, tags=_make_tags_mock(matched=["swiftui"]))
        loader.load("import SwiftUI", "/src/Foo.swift")
        rules.load_detection_rules.assert_called_once_with(["swiftui"])


class TestLLMReviewer(unittest.TestCase):
    def test_returns_violations_when_runner_and_parser_succeed(self):
        reviewer, _ = _make_reviewer(runner_result='{"violations": []}', parse_result=[])
        self.assertEqual(reviewer.review("prompt", "/src/Foo.swift"), [])

    def test_raises_and_logs_when_runner_returns_empty(self):
        reviewer, logger = _make_reviewer(runner_result=None)
        with self.assertRaises(RuntimeError):
            reviewer.review("prompt", "/src/Foo.swift")
        logger.log.assert_called_once()

    def test_raises_and_logs_when_runner_raises(self):
        reviewer, logger = _make_reviewer(runner_raises=RuntimeError("timeout"))
        with self.assertRaises(RuntimeError):
            reviewer.review("prompt", "/src/Foo.swift")
        logger.log.assert_called_once()

    def test_returns_none_and_logs_when_parser_returns_none(self):
        reviewer, logger = _make_reviewer(runner_result='bad json', parse_result=None)
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
        principles = [{"name": "srp", "full_content": "srp detection rules"}]
        prompt = self.builder.build(principles, "code here", "/src/Foo.swift", "")
        self.assertNotIn("srp detection rules", prompt)

    def test_session_id_header_present_when_provided(self):
        prompt = self.builder.build([], "code", "/src/Foo.swift", "session-abc")
        self.assertTrue(prompt.startswith("# spawned-by: session-abc\n"))

    def test_session_id_header_absent_when_empty(self):
        prompt = self.builder.build([], "code", "/src/Foo.swift", "")
        self.assertNotIn("spawned-by", prompt)

    def test_dry_search_instructions_include_query_and_output_directory(self):
        prompt = self.builder.build(
            [],
            "code",
            "/src/Foo.swift",
            "",
            output_dir="/health/run",
        )

        self.assertIn("`query`: the aggregated space-separated query", prompt)
        self.assertIn("`output_dir`: `/health/run`", prompt)
        self.assertIn("Do not pass the aggregated query as one entry in `tags`", prompt)


class TestCheck(unittest.TestCase):
    """Tests for the full _check pipeline, always using the Claude backend."""

    def test_returns_violations_list_when_gateway_reports_findings(self):
        mock_violations = [
            {"principle": "SRP", "metric_id": "SRP-2",
             "issue": "SRP-2: /src/Foo.swift, unit Foo — cohesion_groups >= 2 (measured: cohesion_groups=2)\n    -> Call mcp__docs__load_fix_for_violation(SRP-2) for fix guidance",
             "fix": "Call mcp__docs__load_fix_for_violation(SRP-2) for guidance."},
            {"principle": "OCP", "metric_id": "OCP-1",
             "issue": "OCP-1: /src/Foo.swift, unit Foo — sealed_variation_points >= 1 (measured: sealed_variation_points=2)\n    -> Call mcp__docs__load_fix_for_violation(OCP-1) for fix guidance",
             "fix": "Call mcp__docs__load_fix_for_violation(OCP-1) for guidance."},
        ]
        with _claude_backend_patch(), \
             patch("hook_utils.subprocess.run", side_effect=_make_check_pipeline()), \
             patch("hc_checker.FileOutputReader.read_violations", return_value=mock_violations):
            result = hook._check(LONG_SWIFT, "/src/Foo.swift", "Swift", "test-session")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["principle"], "SRP")

    def test_returns_empty_list_when_no_findings(self):
        with _claude_backend_patch(), \
             patch("hook_utils.subprocess.run", side_effect=_make_check_pipeline()), \
             patch("hc_checker.FileOutputReader.read_violations", return_value=[]):
            result = hook._check(LONG_SWIFT, "/src/Foo.swift", "Swift", "test-session")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_raises_on_gateway_failure(self):
        from hook_utils import SubprocessError
        with _claude_backend_patch(), \
             patch("hook_utils.subprocess.run", return_value=make_subprocess_mock(1, {})):
            with self.assertRaises(SubprocessError):
                hook._check(LONG_SWIFT, "/src/Foo.swift", "Swift", "test-session")


class TestSupportedExtensions(unittest.TestCase):
    def test_known_extensions_map_to_expected_languages(self):
        self.assertEqual(hook.SUPPORTED_EXTENSIONS.get(".py"), "Python")
        self.assertEqual(hook.SUPPORTED_EXTENSIONS.get(".swift"), "Swift")
        self.assertIsNone(hook.SUPPORTED_EXTENSIONS.get(".js"))


if __name__ == "__main__":
    unittest.main()
