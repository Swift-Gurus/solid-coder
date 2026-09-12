"""Tests flow-based prospective source health checking."""

import unittest
from pathlib import Path
from unittest.mock import MagicMock

from _path_bootstrap import ensure_on_path


ensure_on_path(
    Path(__file__).resolve().parents[3] / "mcp-server",
    Path(__file__).resolve().parent,
)

from harness.flow_start_result import FlowStartResult  # noqa: E402
from harness.flow_status_result import FlowStatusResult  # noqa: E402
from review.prepare_review_input import PrepareReviewInput  # noqa: E402
from source.text_analysis_source import TextAnalysisSource  # noqa: E402
from workflow_health_checker import WorkflowHealthChecker  # noqa: E402


"""
solid-name: TestWorkflowHealthChecker
solid-category: unit-test
solid-spec: [SPEC-036, SPEC-041]
solid-description: Proves the gate owns flow startup and trusts only terminal persisted review results.
"""
class TestWorkflowHealthChecker(unittest.TestCase):
    def setUp(self) -> None:
        self.flow = MagicMock()
        self.renderer = MagicMock()
        self.runner = MagicMock()
        self.result_reader = MagicMock()
        self.violation_selector = MagicMock()
        self.input_builder = MagicMock()
        self.prompt_builder = MagicMock()
        self.review_input = PrepareReviewInput(
            target=TextAnalysisSource(
                text="struct NewFeature {}",
                virtual_path="/project/Sources/NewFeature.swift",
            )
        )
        self.input_builder.build.return_value = self.review_input
        self.flow.flow_start.return_value = FlowStartResult(
            run_id="gate-run",
            steps=[],
            isolated=True,
        )
        self.renderer.render_start.return_value = "first ready review step"
        self.prompt_builder.build.return_value = "bootstrap prompt"
        self.runner.run.return_value = "Flow complete."
        self.flow.flow_status.return_value = FlowStatusResult(
            flow="SOLID Gate on Write",
            run_id="gate-run",
            status="done",
            turn_count=3,
            max_turns=500,
            completed=["rule.metric"],
            running=[],
            pending=[],
        )
        self.review_result = MagicMock()
        self.result_reader.read.return_value = self.review_result
        self.violations = [MagicMock()]
        self.violation_selector.select.return_value = self.violations
        self.sut = WorkflowHealthChecker(
            flow=self.flow,
            renderer=self.renderer,
            runner=self.runner,
            result_reader=self.result_reader,
            violation_selector=self.violation_selector,
            input_builder=self.input_builder,
            prompt_builder=self.prompt_builder,
            timeout_seconds=321,
        )

    def test_returns_severe_violations_from_terminal_persisted_result(self) -> None:
        result = self.sut.check(
            content="struct NewFeature {}",
            path="/project/Sources/NewFeature.swift",
            language="Swift",
            parent_session_id="parent-session",
        )

        self.assertIs(result, self.violations)
        self.input_builder.build.assert_called_once_with(
            "struct NewFeature {}",
            "/project/Sources/NewFeature.swift",
            None,
        )
        self.flow.flow_start.assert_called_once_with(
            "solid-gate-on-write",
            params=self.review_input.model_dump(mode="json"),
            isolated=True,
        )
        self.renderer.render_start.assert_called_once_with(
            self.flow.flow_start.return_value
        )
        self.prompt_builder.build.assert_called_once_with(
            content="struct NewFeature {}",
            path="/project/Sources/NewFeature.swift",
            parent_session_id="parent-session",
            run_id="gate-run",
            first_step="first ready review step",
        )
        self.runner.run.assert_called_once_with("bootstrap prompt", timeout=321)
        self.flow.flow_status.assert_called_once_with("gate-run")
        self.result_reader.read.assert_called_once_with("gate-run")
        self.violation_selector.select.assert_called_once_with(self.review_result)

    def test_rejects_nonterminal_child_session(self) -> None:
        self.flow.flow_status.return_value = FlowStatusResult(
            flow="SOLID Gate on Write",
            run_id="gate-run",
            status="ready",
            turn_count=1,
            max_turns=500,
            completed=[],
            running=[],
            pending=["rule.metric"],
        )

        with self.assertRaisesRegex(RuntimeError, "did not complete"):
            self.sut.check(
                content="struct NewFeature {}",
                path="/project/Sources/NewFeature.swift",
                language="Swift",
                parent_session_id="parent-session",
            )

        self.result_reader.read.assert_not_called()

    def test_rejects_failed_flow_start(self) -> None:
        self.flow.flow_start.return_value = FlowStartResult(
            run_id="",
            steps=[],
            error="workflow unavailable",
            isolated=True,
        )

        with self.assertRaisesRegex(RuntimeError, "workflow unavailable"):
            self.sut.check(
                content="struct NewFeature {}",
                path="/project/Sources/NewFeature.swift",
                language="Swift",
                parent_session_id="parent-session",
            )

        self.runner.run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
