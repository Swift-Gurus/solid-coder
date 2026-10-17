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
from codex_flow_continuation_instruction_builder import (  # noqa: E402
    CodexFlowContinuationInstructionBuilder,
)
from gate_flow_prompt_builder import GateFlowPromptBuilder  # noqa: E402
from review.prepare_review_input import PrepareReviewInput  # noqa: E402
from source.text_analysis_source import TextAnalysisSource  # noqa: E402
from workflow_health_checker import WorkflowHealthChecker  # noqa: E402
from health_check_outcome import HealthCheckOutcome
from source.analysis.operations.source_introduction_evidence import SourceIntroductionEvidence


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
        self.assessor = MagicMock()
        self.introductions = MagicMock()
        self.logger = MagicMock()
        self.proof = SourceIntroductionEvidence(reasoning="Compared source versions.", evidence="Source hashes.")
        self.introductions.execute.return_value = self.proof
        self.input_builder = MagicMock()
        self.continuation_builder = CodexFlowContinuationInstructionBuilder()
        self.prompt_builder = GateFlowPromptBuilder(
            continuation_instruction_builder=self.continuation_builder,
        )
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
        self.outcome = HealthCheckOutcome(introduction_evidence=self.proof)
        self.assessor.assess.return_value = self.outcome
        self.sut = WorkflowHealthChecker(
            flow=self.flow,
            renderer=self.renderer,
            runner=self.runner,
            result_reader=self.result_reader,
            assessor=self.assessor,
            introductions=self.introductions,
            logger=self.logger,
            input_builder=self.input_builder,
            prompt_builder=self.prompt_builder,
            timeout_seconds=321,
        )

    def test_returns_assessed_terminal_result_with_source_verification_audit(self) -> None:
        result = self.sut.check(
            content="struct NewFeature {}",
            path="/project/Sources/NewFeature.swift",
            language="Swift",
            parent_session_id="parent-session",
        )

        self.assertIs(result, self.outcome)
        self.introductions.execute.assert_called_once_with(self.review_input.target)
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
        self.runner.run.assert_called_once()
        prompt = self.runner.run.call_args.args[0]
        self.assertEqual(prompt.count("struct NewFeature {}"), 1)
        self.assertTrue(prompt.startswith("# spawned-by: parent-session\n"))
        self.assertIn("/project/Sources/NewFeature.swift", prompt)
        self.assertIn("first ready review step", prompt)
        self.assertIn("The server has already started the isolated review run", prompt)
        self.assertTrue(prompt.endswith(self.continuation_builder.build("gate-run")))
        self.runner.run.assert_called_once_with(prompt, timeout=321)
        self.flow.flow_status.assert_called_once_with("gate-run")
        self.result_reader.read.assert_called_once_with("gate-run")
        self.assessor.assess.assert_called_once_with(self.review_result, self.proof)
        self.logger.log.assert_called_once_with(
            f"gate_review_outcome run_id=gate-run {self.outcome.model_dump_json()}"
        )

    def test_original_source_verification_precedes_the_child_session(self) -> None:
        calls = MagicMock()
        calls.attach_mock(self.introductions.execute, "verify")
        calls.attach_mock(self.runner.run, "run")

        self.sut.check("struct NewFeature {}", "/project/Sources/NewFeature.swift", "Swift", "parent")

        self.assertEqual([call[0] for call in calls.mock_calls], ["verify", "run"])

    def test_rejects_nonterminal_child_session(self) -> None:
        self.runner.run.return_value = (
            "Script failed\nScript error:\nSyntaxError: Unexpected string"
        )
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

        with self.assertRaises(RuntimeError) as raised:
            self.sut.check(
                content="struct NewFeature {}",
                path="/project/Sources/NewFeature.swift",
                language="Swift",
                parent_session_id="parent-session",
            )

        message = str(raised.exception)
        self.assertIn("Gate workflow did not complete: ready", message)
        self.assertIn("SyntaxError: Unexpected string", message)
        self.assertIn("Pending workflow steps: rule.metric", message)
        self.assertIn("Retry the same write", message)
        self.result_reader.read.assert_not_called()

    def test_propagates_child_runner_error_with_retry_action(self) -> None:
        self.runner.run.side_effect = RuntimeError(
            "Script failed: SyntaxError: Unexpected string"
        )
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

        with self.assertRaises(RuntimeError) as raised:
            self.sut.check(
                content="struct NewFeature {}",
                path="/project/Sources/NewFeature.swift",
                language="Swift",
                parent_session_id="parent-session",
            )

        message = str(raised.exception)
        self.assertIn("Gate workflow did not complete: ready", message)
        self.assertIn("SyntaxError: Unexpected string", message)
        self.assertIn("Pending workflow steps: rule.metric", message)
        self.assertIn("Retry the same write", message)
        self.assertIn("new isolated review", message)
        self.flow.flow_status.assert_called_once_with("gate-run")

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
