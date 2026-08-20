"""
solid-name: test_isp_applicability_flow
solid-category: integration-test
solid-spec: [SPEC-039]
solid-description: Verifies a non-protocol fixture skips every ISP step without starting a model session or publishing an ISP result.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))

from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory  # noqa: E402
from harness.runs_base_dir_resolver import RunsBaseDirResolver  # noqa: E402
from harness.static_session_id_reader import StaticSessionIdReader  # noqa: E402


class TestISPApplicabilityFlow(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.temporary_root = Path(temporary.name)
        self.run_root = self.temporary_root / "project"
        self.plugin_root = self.temporary_root / "plugin"
        self.workflow_path = self._prepare_isolated_catalog()
        self.fixture_path = (
            _PROJECT_ROOT
            / "tests"
            / "principles"
            / "ISP"
            / "fixtures"
            / "fixture-3.swift"
        )
        self.sut = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.run_root
            ),
            plugin_root=self.plugin_root,
            session_reader=StaticSessionIdReader("spec-039-isp-skip-test"),
        ).build()

    def test_non_protocol_fixture_skips_isp_without_starting_a_session(self) -> None:
        result = self.sut.flow_start(
            str(self.workflow_path),
            params={
                "review_unit": {
                    "file_extension": ".swift",
                    "unit_kind": "class",
                    "tags": [],
                    "content": self.fixture_path.read_text(encoding="utf-8"),
                }
            },
        )

        self.assertEqual(result.status, "done")
        self.assertEqual(result.steps, [])
        events = self._events(result.run_id)
        skipped = [event for event in events if event["event"] == "step_skipped"]
        self.assertEqual(
            [event["local_step_id"] for event in skipped],
            [
                "width",
                "min_coverage",
                "cohesion_groups",
                "classify_exception",
            ],
        )
        self.assertTrue(
            all(event["workflow_instance_id"] is not None for event in skipped)
        )
        self.assertTrue(all(not event["evidence"]["matched"] for event in skipped))
        self.assertTrue(
            all(
                "params.review_unit.unit_kind" in json.dumps(event["condition"])
                for event in skipped
            )
        )
        skipped_instances = {event["instance_id"] for event in skipped}
        self.assertFalse(
            any(
                event.get("event") == "session_step_recorded"
                and event.get("instance_id") in skipped_instances
                for event in events
            )
        )
        self.assertFalse(
            (self.run_root / "runs" / result.run_id / "results" / "review" / "isp").exists()
        )

    def _prepare_isolated_catalog(self) -> Path:
        rule_package = self.plugin_root / "workflows" / "review" / "rules" / "isp"
        rule_package.mkdir(parents=True)
        shutil.copy2(
            _PROJECT_ROOT / "workflows" / "review" / "rules" / "isp" / "workflow.yaml",
            rule_package / "workflow.yaml",
        )
        bundle = self.plugin_root / "workflows" / "review" / "bundles" / "isp-skip"
        bundle.mkdir(parents=True)
        workflow_path = bundle / "workflow.yaml"
        workflow_path.write_text(
            textwrap.dedent(
                """
                id: isp-skip-test
                name: ISP Skip Test
                max_turns: 5
                steps:
                  - include:
                      rules: all
                    as: rule_reviews
                    with:
                      review_unit: "{{params.review_unit}}"
                """
            ),
            encoding="utf-8",
        )
        return workflow_path

    def _events(self, run_id: str) -> list[dict[str, object]]:
        return [
            json.loads(line)
            for line in (
                self.run_root / "runs" / run_id / "events.jsonl"
            ).read_text(encoding="utf-8").splitlines()
        ]
