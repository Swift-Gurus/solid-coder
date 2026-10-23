"""
solid-name: TestFrontmatterSourceBackedFlow
solid-category: integration-test
solid-spec: [SPEC-069]
solid-description: Verifies the real metadata workflow runs mechanical checks without model turns and validates description batches before scoring.
"""

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.project_context import ProjectDirectory
from harness.runs_base_dir_resolver import RunsBaseDirResolver
from harness.static_session_id_reader import StaticSessionIdReader
from source.frontmatter.frontmatter_preparation import FrontmatterPreparation
from source.source_operation_registrations_factory import (
    SourceOperationRegistrationsFactory,
)


class TestFrontmatterSourceBackedFlow(unittest.TestCase):
    def setUp(self) -> None:
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.repo = Path(__file__).resolve().parents[3]
        self.sut = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(project_dir_fn=lambda: self.root),
            plugin_root=self.repo,
            project_directory=ProjectDirectory(path=self.root),
            session_reader=StaticSessionIdReader("frontmatter-spec-069"),
            operation_registrations=SourceOperationRegistrationsFactory(
                ProjectDirectory(path=self.root)
            ).make(),
        ).build()

    def test_missing_frontmatter_completes_with_no_model_steps(self) -> None:
        result = self._start("struct Target {}")
        self.assertEqual(result.status, "done", result.error)
        self.assertEqual(result.steps, [])
        self.assertEqual(self._values(result.run_id), [1, 0, 0, 0, 0])

    def test_project_policy_overrides_the_bundled_missing_metadata_threshold(
        self,
    ) -> None:
        policy = self.root / ".solid-coder/policies/review.yaml"
        policy.parent.mkdir(parents=True)
        policy.write_text(
            "version: 1\nrules:\n  - workflow_id: frontmatter\n"
            "    metrics:\n      - id: FM-1\n        scoring:\n"
            "          severe: {operator: greater_than_or_equal, value: 2}\n"
            "        reason: Permit one missing metadata block in this test project.\n",
        )
        result = self._start("struct Target {}")
        self.assertEqual(result.status, "done", result.error)
        self.assertEqual(self._values(result.run_id), [1, 0, 0, 0, 0])
        result_file = next(
            (self.root / "runs" / result.run_id / "results/review/frontmatter").rglob(
                "result.json"
            )
        )
        scored = json.loads(result_file.read_text())
        self.assertEqual(scored["metrics"][0]["severity"], "COMPLIANT")
        self.assertEqual(scored["severity"], "COMPLIANT")

    def test_description_batch_partial_submission_preserves_missing_target_then_scores(
        self,
    ) -> None:
        ready = self._start(self._code("Alpha") + "\n" + self._code("Beta"))
        self.assertEqual(
            [step.step_id for step in ready.steps],
            ["classify_descriptions", "classify_descriptions"],
        )
        self.assertNotIn("struct Alpha", ready.steps[0].prompt)
        self.assertIn("Provides deliveries.", ready.steps[0].prompt)
        partial = self.sut.flow_next(
            {ready.steps[0].batch.label: self._judgment(ready.steps[0])}
        )
        self.assertEqual(partial.status, "ready", partial.error)
        self.assertTrue(partial.steps[0].batch.label.startswith("Beta (line "))
        self.assertEqual(len(partial.steps), 1)
        done = self.sut.flow_next(
            {partial.steps[0].batch.label: self._judgment(partial.steps[0])}
        )
        self.assertEqual(done.status, "done", done.error)
        self.assertEqual(self._values(ready.run_id), [0, 0, 0, 0, 0])

    def test_missing_evidence_is_rejected_then_correction_completes(self) -> None:
        ready = self._start(self._code("Alpha"))
        output = self._judgment(ready.steps[0])
        del output["classification"]["additional_info"]["evidence"]
        rejected = self.sut.flow_next({ready.steps[0].batch.label: output})
        self.assertEqual(rejected.status, "ready", rejected.error)
        self.assertIn("evidence", rejected.steps[0].rejection_reason)
        done = self.sut.flow_next(
            {rejected.steps[0].batch.label: self._judgment(rejected.steps[0])}
        )
        self.assertEqual(done.status, "done", done.error)

    def test_structural_description_failure_needs_no_model_judgment(self) -> None:
        result = self._start(
            "// solid-name: Target\n// solid-category: abstraction\n// solid-description: Provides an interface.\nprotocol Target {}"
        )
        self.assertEqual(result.status, "done", result.error)
        self.assertEqual(self._values(result.run_id), [0, 0, 0, 0, 1])

    def _start(self, code: str):
        result = self.sut.flow_start(
            "frontmatter",
            {
                "review_unit": {
                    "target": {
                        "name": "Unwritten",
                        "code": code,
                        "source_identity": str(self.root / "Unwritten.swift"),
                    }
                }
            },
        )
        self.run_id = result.run_id
        return result

    def _code(self, name: str) -> str:
        return f"// solid-name: {name}\n// solid-category: service\n// solid-description: Provides deliveries.\nstruct {name} {{}}"

    def _judgment(self, step):
        events = [
            json.loads(line)
            for line in (self.root / "runs" / self.run_id / "events.jsonl")
            .read_text()
            .splitlines()
        ]
        event = next(
            entry
            for entry in events
            if entry.get("event") == "step_completed"
            and entry["step_id"] == "prepare_frontmatter"
        )
        prepared = FrontmatterPreparation.model_validate(event["outputs"])
        target = next(
            entry for entry in prepared.descriptions if entry.label == step.batch.label
        )
        return {
            "classification": {
                "declaration_id": target.declaration_id,
                "classification": "CAPABILITY",
                "additional_info": {
                    "reasoning": "Describes the capability.",
                    "evidence": "Provides deliveries.",
                },
            }
        }

    def _values(self, run_id: str) -> list[int]:
        files = list(
            (self.root / "runs" / run_id / "results/review/frontmatter").rglob(
                "result.json"
            )
        )
        result = json.loads(files[0].read_text())
        return [metric["value"] for metric in result["metrics"]]
