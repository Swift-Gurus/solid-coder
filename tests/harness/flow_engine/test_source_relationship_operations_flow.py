import sys
import tempfile
import unittest
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))

from git_working_tree_fixture import GitWorkingTreeFixture
from harness.event_replayer import EventParser
from harness.project_context import ProjectDirectory
from harness.step_completed_event import StepCompletedEvent
from operation_workflow_integration_driver import OperationWorkflowIntegrationDriver
from source.analysis.matching.source_requirement_matches import SourceRequirementMatches
from source.file_analysis_source import FileAnalysisSource
from source.source_operation_registrations_factory import (
    SourceOperationRegistrationsFactory,
)

"""
solid-name: TestSourceRelationshipOperationsFlow
solid-category: integration-test
solid-spec: [SPEC-057]
solid-description: Verifies source analysis operations execute before combined model work and survive partial submission and replay without rereading source.
"""


class TestSourceRelationshipOperationsFlow(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        GitWorkingTreeFixture(self.root).initialize()
        self.interface = self.root / "Reading.swift"
        self.source = self.root / "Store.swift"
        self.extension = self.root / "Store+Reading.swift"
        self.interface.write_text(
            "protocol Reading { func read(id: Int) -> String }\n", encoding="utf-8"
        )
        self.source.write_text("struct Store: Reading {}\n", encoding="utf-8")
        self.extension.write_text(
            'extension Store { func read(id value: Int) -> String { "ok" } }\n',
            encoding="utf-8",
        )
        self.driver = OperationWorkflowIntegrationDriver(
            project_root=self.root,
            registrations=SourceOperationRegistrationsFactory(
                ProjectDirectory(path=self.root)
            ).make(),
        )
        self.driver.write_workflow(
            (
                Path(__file__).parent
                / "fixtures"
                / "source_relationship_operations"
                / "workflow.yaml"
            ).read_text(encoding="utf-8")
        )
        child = self.root / "workflows" / "source-matching"
        child.mkdir(parents=True)
        (child / "workflow.yaml").write_text(
            (
                Path(__file__).parent
                / "fixtures"
                / "source_relationship_operations"
                / "matching.yaml"
            ).read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    def start(self):
        self.run_id = self.driver.start().run_id
        ready = self.driver.advance(
            {
                "source-relationships": {
                    "source-relationships": {
                        "select": {
                            "sources": [
                                FileAnalysisSource(path=path).model_dump(mode="json")
                                for path in [
                                    self.interface,
                                    self.source,
                                    self.extension,
                                ]
                            ]
                        },
                    }
                }
            }
        )
        self.assertIsNone(ready.error, ready.error)
        self.assignment = ready.steps[0].batch
        return ready

    def completed(self, run_id: str) -> list[StepCompletedEvent]:
        records = EventParser().parse(
            (self.root / "runs" / run_id / "events.jsonl").read_text().splitlines()
        )
        return [
            StepCompletedEvent.model_validate(record)
            for record in records
            if record.get("event") == "step_completed"
        ]

    def matching_result(self, run_id: str) -> SourceRequirementMatches:
        event = next(
            item for item in self.completed(run_id) if item.local_step_id == "match"
        )
        return SourceRequirementMatches.model_validate(event.outputs)

    def test_engine_operations_finish_before_combined_classification_is_presented(
        self,
    ) -> None:
        started = self.start()

        self.assertIsNone(started.error, started.error)
        self.assertEqual(
            [step.step_id for step in started.steps],
            ["checks-1.classify", "checks-1.audit"],
        )
        self.assertEqual(
            [event.step_id for event in self.completed(self.run_id)],
            ["select", "inspect", "inspect", "inspect", "link", "checks-1.match"],
        )
        self.assertEqual(
            self.matching_result(self.run_id).matches[0].status.value, "candidate"
        )

    def test_fan_in_preserves_complete_source_snapshots_in_input_order(self) -> None:
        self.start()

        inventory = self.matching_result(self.run_id).inventory

        self.assertEqual(
            [item.source_identity for item in inventory.analyses],
            [str(self.interface), str(self.source), str(self.extension)],
        )
        self.assertEqual(inventory.verification, "unverified_candidates")

    def test_combined_submission_completes_without_resubmitting_operation_outputs(
        self,
    ) -> None:
        self.start()

        finished = self.driver.advance(
            {
                self.assignment.label: {
                    self.assignment.workflow_alias: {
                        "classify": {"meaningful": True},
                        "audit": {"sufficient": True},
                    }
                }
            }
        )

        self.assertEqual(finished.status, "done", finished.error)
        self.assertEqual(
            [event.step_id for event in self.completed(self.run_id)],
            [
                "select",
                "inspect",
                "inspect",
                "inspect",
                "link",
                "checks-1.match",
                "checks-1.classify",
                "checks-1.audit",
            ],
        )

    def test_replay_restores_matching_evidence_after_source_is_removed(self) -> None:
        self.start()
        before = self.matching_result(self.run_id)
        self.interface.unlink()
        self.source.unlink()
        self.extension.unlink()

        finished = self.driver.advance(
            {
                self.assignment.label: {
                    self.assignment.workflow_alias: {
                        "classify": {"meaningful": True},
                        "audit": {"sufficient": True},
                    }
                }
            }
        )

        self.assertEqual(finished.status, "done", finished.error)
        self.assertEqual(self.matching_result(self.run_id), before)
        self.assertEqual(
            [event.step_id for event in self.completed(self.run_id)].count("inspect"), 3
        )

    def test_partial_combined_submission_preserves_operations_and_accepted_sibling(
        self,
    ) -> None:
        self.start()

        pending = self.driver.advance(
            {
                self.assignment.label: {
                    self.assignment.workflow_alias: {
                        "classify": {"meaningful": True},
                    }
                }
            }
        )
        finished = self.driver.advance(
            {
                self.assignment.label: {
                    self.assignment.workflow_alias: {
                        "audit": {"sufficient": True},
                    }
                }
            }
        )

        self.assertEqual([step.step_id for step in pending.steps], ["checks-1.audit"])
        self.assertEqual(finished.status, "done", finished.error)
        self.assertEqual(
            [event.step_id for event in self.completed(self.run_id)],
            [
                "select",
                "inspect",
                "inspect",
                "inspect",
                "link",
                "checks-1.match",
                "checks-1.classify",
                "checks-1.audit",
            ],
        )

    def test_invalid_combined_sibling_retries_without_repeating_matching(self) -> None:
        self.start()

        pending = self.driver.advance(
            {
                self.assignment.label: {
                    self.assignment.workflow_alias: {
                        "classify": {"meaningful": "invalid"},
                        "audit": {"sufficient": True},
                    }
                }
            }
        )
        finished = self.driver.advance(
            {
                self.assignment.label: {
                    self.assignment.workflow_alias: {
                        "classify": {"meaningful": True},
                    }
                }
            }
        )

        self.assertEqual(
            [step.step_id for step in pending.steps], ["checks-1.classify"]
        )
        self.assertIn("not of type 'boolean'", pending.steps[0].rejection_reason)
        self.assertEqual(finished.status, "done", finished.error)
        self.assertEqual(
            [event.step_id for event in self.completed(self.run_id)],
            [
                "select",
                "inspect",
                "inspect",
                "inspect",
                "link",
                "checks-1.match",
                "checks-1.audit",
                "checks-1.classify",
            ],
        )

    def test_missing_implementation_remains_unresolved_in_persisted_operation_output(
        self,
    ) -> None:
        self.extension.write_text("extension Store {}\n", encoding="utf-8")

        started = self.start()

        self.assertIsNone(started.error, started.error)
        self.assertEqual(
            self.matching_result(self.run_id).matches[0].status.value, "unresolved"
        )
        self.assertEqual(self.matching_result(self.run_id).matches[0].candidates, [])
