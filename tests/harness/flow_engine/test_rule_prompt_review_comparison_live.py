"""Runs the YAML-only rule-prompt review experiment through Codex Terra."""

import json
import sys
from collections import Counter
from pathlib import Path

_HARNESS = Path(__file__).resolve().parents[1]
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
for _directory in (_HARNESS, _PROJECT_ROOT / "mcp-server"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

from codex_test_base import CodexTestBase  # noqa: E402
from live_session_artifact_scope import LiveSessionArtifactScope  # noqa: E402
from live_workflow_e2e_live_base import LiveWorkflowE2ELiveBase  # noqa: E402
from live_workflow_scenario import LiveWorkflowScenario  # noqa: E402
from preserved_live_workflow_run import PreservedLiveWorkflowRun  # noqa: E402
from review.prepare_review_input import PrepareReviewInput  # noqa: E402
from review_comparison_source_project import ReviewComparisonSourceProject  # noqa: E402
from source.file_analysis_source import FileAnalysisSource  # noqa: E402


"""
solid-name: TestCodexRulePromptReviewComparisonLive
solid-category: integration-test
solid-spec: [SPEC-036, SPEC-041]
solid-description: Proves the YAML-only aggregate-rule experiment completes the controlled full-review fixture with a bounded model-step count.
"""
class TestCodexRulePromptReviewComparisonLive(
    CodexTestBase,
    LiveWorkflowE2ELiveBase,
):
    __test__ = True
    PROJECT_ROOT = _PROJECT_ROOT

    def setUp(self) -> None:
        self._source_project = ReviewComparisonSourceProject.create()
        self.addCleanup(self._source_project.cleanup)
        super().setUp()

    @property
    def execution_project_root(self) -> Path:
        return self._source_project.root

    @property
    def scenario(self) -> LiveWorkflowScenario:
        source = self._source_project.review_target.read_text(encoding="utf-8")
        return LiveWorkflowScenario(
            workflow_id="rule-prompt-file-review",
            parameters=PrepareReviewInput(
                target=FileAnalysisSource(path=self._source_project.review_target)
            ),
            artifact_scope=LiveSessionArtifactScope(
                domain="comparison",
                scenario="rule-prompt-smoke",
            ),
            model_context=f"Source under review:\n```swift\n{source}\n```",
        )

    def assert_workflow(self, run: PreservedLiveWorkflowRun) -> None:
        events = [
            json.loads(line)
            for line in (run.run_directory / "events.jsonl").read_text().splitlines()
            if line.strip()
        ]
        self.assertEqual(events[-1]["event"], "run_completed")
        self.assertFalse(
            {event.get("event") for event in events}
            & {"step_attempt_failed", "step_rejected", "run_failed"}
        )
        model_steps = [
            event["local_step_id"]
            for event in events
            if event.get("event") == "step_completed"
            and event.get("session_id") != "engine"
        ]
        self.assertEqual(
            Counter(model_steps),
            Counter({
                "assess_code_smells": 1,
                "assess_frontmatter": 1,
                "assess_srp": 1,
                "assess_ocp": 2,
                "assess_lsp": 2,
                "assess_isp": 1,
                "generate_terms": 2,
                "assess_dry": 2,
            }),
        )


if __name__ == "__main__":
    import unittest

    unittest.main()
