"""Verifies explicit principle scoping through the real health-check boundary."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
for _directory in (
    _PROJECT_ROOT / "mcp-server",
    _PROJECT_ROOT / "mcp-server" / "health",
    _PROJECT_ROOT / "mcp-server" / "health" / "codex",
    _PROJECT_ROOT / "mcp-server" / "health" / "config",
    _PROJECT_ROOT / "mcp-server" / "health" / "llm",
    _PROJECT_ROOT / "mcp-server" / "gate",
    _PROJECT_ROOT / "mcp-server" / "output",
    _PROJECT_ROOT / "mcp-server" / "patch",
    _PROJECT_ROOT / "mcp-server" / "session",
    _PROJECT_ROOT / "mcp-server" / "utils",
):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

import code_health_check  # noqa: E402
from code_health_check_request import CodeHealthCheckRequest  # noqa: E402
from code_health_check_service import CodeHealthCheckService  # noqa: E402
from hc_checker import LLMHealthChecker  # noqa: E402
from health_prompt_builder import HealthPromptBuilder  # noqa: E402
from principles_loader import PrinciplesLoader  # noqa: E402


"""
solid-name: TestPrincipleScopedHealthCheck
solid-category: unit-test
solid-spec: [SPEC-041]
solid-description: Proves declared comparison principles reach the real checker and exclusively define its model-facing prompt.
"""
class TestPrincipleScopedHealthCheck(unittest.TestCase):
    def test_check_forwards_declared_principles_in_typed_request(self) -> None:
        service = MagicMock()
        service.check.return_value = []

        code_health_check.CodeHealthCheck(service).check(
            content="final class Example {}",
            path="/project/Example.swift",
            language="Swift",
            parent_session_id="comparison-session",
            principle_names=["SRP"],
        )

        request = service.check.call_args.args[0]
        self.assertEqual(request.principle_names, ["SRP"])

    def test_loader_returns_only_declared_principles_in_declared_order(self) -> None:
        rules = MagicMock()
        rules.get_candidate_tags.return_value = []
        rules.load_detection_rules.return_value = {
            "principles": [
                {"name": "ocp", "content": "OCP instructions"},
                {"name": "srp", "content": "SRP instructions"},
                {"name": "dry", "content": "DRY instructions"},
            ]
        }
        tags = MagicMock()
        tags.detect.return_value = []

        principles = PrinciplesLoader(rules=rules, tags=tags).load(
            "final class Example {}",
            "/project/Example.swift",
            principle_names=["SRP", "OCP"],
        )

        self.assertEqual(
            [principle["name"] for principle in principles],
            ["srp", "ocp"],
        )

    def test_srp_only_prompt_does_not_require_dry_analysis(self) -> None:
        prompt = HealthPromptBuilder().build(
            principles=[{"name": "srp", "content": "SRP instructions"}],
            content="final class Example {}",
            path="/project/Example.swift",
            parent_session_id="comparison-session",
            output_dir="/tmp/health-run",
        )

        self.assertIn("SRP instructions", prompt)
        self.assertNotIn("search_codebase", prompt)
        self.assertIn("after completing step 1", prompt)
        self.assertNotIn("after completing step 2", prompt)

    def test_dry_prompt_submits_after_the_search_step(self) -> None:
        prompt = HealthPromptBuilder().build(
            principles=[{"name": "dry", "content": "DRY instructions"}],
            content="final class Example {}",
            path="/project/Example.swift",
            parent_session_id="comparison-session",
            output_dir="/tmp/health-run",
        )

        self.assertIn("search_codebase", prompt)
        self.assertIn("after completing step 2", prompt)

    def test_loader_rejects_a_declared_principle_that_was_not_loaded(self) -> None:
        rules = MagicMock()
        rules.get_candidate_tags.return_value = []
        rules.load_detection_rules.return_value = {
            "principles": [{"name": "srp", "content": "SRP instructions"}]
        }
        tags = MagicMock()
        tags.detect.return_value = []

        with self.assertRaisesRegex(ValueError, "OCP"):
            PrinciplesLoader(rules=rules, tags=tags).load(
                "final class Example {}",
                "/project/Example.swift",
                principle_names=["SRP", "OCP"],
            )

    def test_service_passes_declared_principles_to_real_checker_contract(self) -> None:
        checker = MagicMock()
        checker.check.return_value = []
        checker_factory = MagicMock()
        checker_factory.make.return_value = checker
        service = CodeHealthCheckService(
            checker_factory=checker_factory,
        )

        service.check(CodeHealthCheckRequest(
            content="final class Example {}",
            path="/project/Example.swift",
            language="Swift",
            parent_session_id="comparison-session",
            principle_names=["SRP"],
        ))

        checker.check.assert_called_once_with(
            "final class Example {}",
            "/project/Example.swift",
            "Swift",
            "comparison-session",
            patch_context=None,
            principle_names=["SRP"],
        )

    def test_llm_checker_scopes_loader_before_building_prompt(self) -> None:
        loader = MagicMock()
        loader.load.return_value = [
            {"name": "srp", "content": "SRP instructions"}
        ]
        builder = MagicMock()
        builder.build.return_value = "SRP-only prompt"
        reviewer = MagicMock()
        reviewer.review.return_value = []
        path_resolver = MagicMock()
        path_resolver.resolve.return_value = "/tmp/health-run"
        checker = LLMHealthChecker(
            loader=loader,
            builder=builder,
            reviewer=reviewer,
            path_resolver=path_resolver,
        )

        checker.check(
            "final class Example {}",
            "/project/Example.swift",
            "Swift",
            "comparison-session",
            principle_names=["SRP"],
        )

        loader.load.assert_called_once_with(
            "final class Example {}",
            "/project/Example.swift",
            ["SRP"],
        )


if __name__ == "__main__":
    unittest.main()
