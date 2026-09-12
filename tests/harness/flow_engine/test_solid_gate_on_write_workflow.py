"""Tests the packaged prospective-write review workflow."""

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_TEST_HARNESS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))
sys.path.insert(0, str(_TEST_HARNESS_ROOT))

from bundled_review_rule_policy_writer import (  # noqa: E402
    BundledReviewRulePolicyWriter,
)
from harness.flow_run_orchestrator_factory import (  # noqa: E402
    FlowRunOrchestratorFactory,
)
from harness.runs_base_dir_resolver import RunsBaseDirResolver  # noqa: E402
from review.review_operation_registrations_factory import (  # noqa: E402
    ReviewOperationRegistrationsFactory,
)
from source.source_operation_registrations_factory import (  # noqa: E402
    SourceOperationRegistrationsFactory,
)


"""
solid-name: TestSolidGateOnWriteWorkflow
solid-category: integration-test
solid-spec: [SPEC-036, SPEC-039, SPEC-041]
solid-description: Proves the packaged gate reviews a nonexistent destination from its prospective buffer and materializes file-scoped test review once.
"""
class TestSolidGateOnWriteWorkflow(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project_root = Path(temporary.name)
        self.target_path = self.project_root / "Tests" / "ProfileTests.swift"
        self.source = textwrap.dedent(
            """
            import Testing

            @Suite struct ProfileLoadingTests {
                @Test func loadsProfile() { #expect(true) }
            }

            @Suite struct ProfileSavingTests {
                @Test func savesProfile() { #expect(true) }
            }
            """
        ).lstrip()
        BundledReviewRulePolicyWriter(
            plugin_root=_PROJECT_ROOT,
            project_root=self.project_root,
        ).write_only("unit-testing")
        registrations = [
            *SourceOperationRegistrationsFactory(
                project_directory=lambda: self.project_root,
            ).make(),
            *ReviewOperationRegistrationsFactory().make(),
        ]
        self.flow = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.project_root,
            ),
            plugin_root=_PROJECT_ROOT,
            project_directory=lambda: self.project_root,
            operation_registrations=registrations,
        ).build()

    def test_reviews_new_file_buffer_without_creating_destination(self) -> None:
        started = self.flow.flow_start(
            "solid-gate-on-write",
            params={
                "target": {
                    "kind": "text",
                    "text": self.source,
                    "virtual_path": str(self.target_path),
                },
                "context_sources": [],
            },
            isolated=True,
        )

        self.assertIsNone(started.error, started.error)
        self.assertFalse(self.target_path.exists())
        self.assertEqual(len(started.steps), 7)
        self.assertTrue(
            all("unit-testing" in step.instance_id for step in started.steps)
        )
        self.assertTrue(
            all(self.source not in step.prompt for step in started.steps)
        )
        self.assertTrue(all(step.batch is not None for step in started.steps))
        self.assertEqual(
            {step.batch.mode.value for step in started.steps},
            {"aggregate"},
        )

    def test_preserves_unsaved_sibling_buffers_as_review_source_context(self) -> None:
        sibling_path = self.project_root / "Sources" / "ProfileStore.swift"
        sibling_source = "struct ProfileStore { func load() async {} }\n"

        started = self.flow.flow_start(
            "solid-gate-on-write",
            params={
                "target": {
                    "kind": "text",
                    "text": self.source,
                    "virtual_path": str(self.target_path),
                },
                "context_sources": [
                    {
                        "kind": "text",
                        "text": sibling_source,
                        "virtual_path": str(sibling_path),
                    }
                ],
            },
            isolated=True,
        )

        self.assertIsNone(started.error, started.error)
        self.assertFalse(self.target_path.exists())
        self.assertFalse(sibling_path.exists())
        events_path = (
            self.project_root
            / "runs"
            / "subagents"
            / started.run_id
            / "events.jsonl"
        )
        prepare_event = next(
            event
            for event in (
                json.loads(line) for line in events_path.read_text().splitlines()
            )
            if event.get("event") == "step_completed"
            and event.get("step_id", "").endswith("prepare_review")
        )
        sources = prepare_event["outputs"]["source_context"]["sources"]
        self.assertEqual(
            [(source["path"], source["content"]) for source in sources],
            [
                (str(self.target_path.resolve()), self.source),
                (str(sibling_path.resolve()), sibling_source),
            ],
        )

    def test_status_replays_the_gate_with_its_persisted_target(self) -> None:
        started = self.flow.flow_start(
            "solid-gate-on-write",
            params={
                "target": {
                    "kind": "text",
                    "text": self.source,
                    "virtual_path": str(self.target_path),
                },
                "context_sources": [],
            },
            isolated=True,
        )

        status = self.flow.flow_status(started.run_id)

        self.assertIsNone(status.error, status.error)
        self.assertEqual(status.status, "in_progress")
        self.assertTrue(status.pending)


if __name__ == "__main__":
    unittest.main()
