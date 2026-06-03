"""
solid-name: TestApplyFlowInvoker
solid-category: unit-test
solid-spec: [SPEC-014]
solid-description: Verifies that the review-apply flow runs a review session, surfaces the resulting findings, and fails when no valid result is produced.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from _path_bootstrap import ensure_on_path

_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parents[2]
_HARNESS_DIR = _PROJECT_ROOT / "tests" / "harness"
_HOOKS_DIR = _PROJECT_ROOT / "hooks"

ensure_on_path(_HARNESS_DIR, _HERE, _HOOKS_DIR)

from apply_flow_invoker import ApplyFlowInvoker, ClaudeReviewSessionRunner, FindingsReader, ReasoningWriter, ReviewArtifactHandler, ReviewInputBuilder  # noqa: E402
from test_fixtures import _make_output_paths, _make_profile  # noqa: E402


def _make_mock(method: str, return_value=None) -> MagicMock:
    mock = MagicMock()
    getattr(mock, method).return_value = return_value
    return mock


def _make_mcp_builder(return_value: str = '{"mcpServers": {}}') -> MagicMock:
    return _make_mock("build", return_value)


def _make_claude_runner(return_value: str | None = "output") -> MagicMock:
    return _make_mock("run_bare", return_value)


class TestClaudeReviewSessionRunner(unittest.TestCase):
    def setUp(self) -> None:
        self._root = Path("/fake/project")
        self._principle = self._root / "references/principles/SRP"

    def _make_runner(self, mcp_return="config_json", claude_return="output"):
        mcp_builder = _make_mcp_builder(mcp_return)
        claude_runner = _make_claude_runner(claude_return)
        return ClaudeReviewSessionRunner(self._root, claude_runner, mcp_builder), mcp_builder, claude_runner

    def _run_execute(self, runner):
        with patch("apply_flow_invoker._build_skill_prompt", return_value="mock-prompt"):
            return runner.execute(self._principle, Path("/input.json"), Path("/output"), timeout=30)

    def test_calls_mcp_config_builder_with_project_root(self):
        runner, mcp_builder, _ = self._make_runner()
        self._run_execute(runner)
        mcp_builder.build.assert_called_once_with(self._root)

    def test_passes_mcp_config_to_claude_runner(self):
        runner, _, claude_runner = self._make_runner(mcp_return="my_config")
        self._run_execute(runner)
        call_kwargs = claude_runner.run_bare.call_args.kwargs
        self.assertEqual(call_kwargs["mcp_config"], "my_config")

    def test_returns_none_when_claude_runner_returns_none(self):
        runner, _, _ = self._make_runner(claude_return=None)
        result = self._run_execute(runner)
        self.assertIsNone(result)

    def test_returns_string_result_from_claude_runner(self):
        runner, _, _ = self._make_runner(claude_return="session output")
        result = self._run_execute(runner)
        self.assertEqual(result, "session output")

    def test_prompt_contains_principle_folder_path(self):
        runner, _, claude_runner = self._make_runner()
        # _build_skill_prompt is called with principle_folder; verify it's invoked correctly
        with patch("apply_flow_invoker._build_skill_prompt", return_value="mock") as mock_build:
            runner.execute(self._principle, Path("/input.json"), Path("/output"), timeout=30)
            args = mock_build.call_args
            self.assertEqual(args.kwargs.get("principle_folder", args.args[1] if len(args.args) > 1 else None), self._principle)


class TestApplyFlowInvokerInvoke(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_ctx = tempfile.TemporaryDirectory()
        self._tmp = Path(self._tmp_ctx.name)
        self._fixture = self._tmp / "fixture.swift"
        self._fixture.write_text("class Foo {}", encoding="utf-8")
        self._output_paths = _make_output_paths(self._tmp)
        self._principle = Path("/fake/project/references/principles/SRP")

    def tearDown(self) -> None:
        self._tmp_ctx.cleanup()

    def _make_invoker(self, session_return: str | None = None, findings: list | None = None):
        artifact_handler = ReviewArtifactHandler(
            input_builder=ReviewInputBuilder(),
            reasoning_writer=ReasoningWriter(),
            findings_reader=FindingsReader(),
        )
        session_runner = MagicMock()
        session_runner.execute.return_value = session_return

        if session_return is not None:
            # The invoker reads from {log_dir}/{fixture_stem}/{NAME}/review-output.json
            review_output = {"findings": findings or []}
            fixture_stem = self._fixture.stem  # "fixture"
            actual_output = self._output_paths.log_dir / fixture_stem / "SRP" / "review-output.json"
            actual_output.parent.mkdir(parents=True, exist_ok=True)
            actual_output.write_text(json.dumps(review_output), encoding="utf-8")

        return ApplyFlowInvoker(self._principle, artifact_handler, session_runner)

    def test_raises_when_session_runner_returns_none(self):
        invoker = self._make_invoker(session_return=None)
        with self.assertRaises(RuntimeError):
            invoker.invoke(self._fixture, self._output_paths, _make_profile(), timeout=30)

    def test_returns_findings_from_review_output(self):
        findings = [{"unit_name": "Foo", "metric_id": "SRP-1", "severity": "SEVERE"}]
        invoker = self._make_invoker(session_return="output", findings=findings)
        result = invoker.invoke(self._fixture, self._output_paths, _make_profile(), timeout=30)
        self.assertEqual(result, findings)

    def test_returns_empty_list_when_no_findings(self):
        invoker = self._make_invoker(session_return="output", findings=[])
        result = invoker.invoke(self._fixture, self._output_paths, _make_profile(), timeout=30)
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
