"""Source-inspection facts remain engine-owned across aggregate replay."""

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.event_replayer import EventParser
from harness.operations.operation_result import OperationResult
from harness.project_context import ProjectDirectory
from harness.step_completed_event import StepCompletedEvent
from operation_workflow_integration_driver import OperationWorkflowIntegrationDriver
from source.analysis.tree_sitter_syntax_parser import TreeSitterSyntaxParser
from source.file_analysis_source import FileAnalysisSource
from source.source_analysis import SourceAnalysis
from source.source_operation_registrations_factory import (
    SourceOperationRegistrationsFactory,
)

"""
solid-name: TestTypeInspectionOperationReplay
solid-category: integration-test
solid-spec: [SPEC-063]
solid-description: Verifies source-inspection evidence persists before aggregated model work and survives partial completion without reparsing changed source.
"""


class TestTypeInspectionOperationReplay(unittest.TestCase):
    def test_partial_aggregate_submission_replays_original_inspections_without_reparsing(
        self,
    ) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            path = root / "Inspect.swift"
            path.write_text(
                "func inspect(_ value: Any) {\n"
                " _ = value as? Model\n"
                " switch value { case is Model: break; default: break }\n"
                " do { try work() } catch let e as Failure { }\n"
                "}\n",
                encoding="utf-8",
            )
            driver = OperationWorkflowIntegrationDriver(
                project_root=root,
                registrations=SourceOperationRegistrationsFactory(
                    ProjectDirectory(path=root)
                ).make(),
            )
            driver.write_workflow("""
id: inspection-facts
name: Inspection facts
max_turns: 5
execution:
  mode: aggregate
presentation:
  mode: combined
steps:
  - id: analyze
    type: operation
    operation: source.analyze
    with:
      source: "{{params.source}}"
  - id: classify
    depends_on: [analyze]
    prompt: Classify the recorded inspection.
    outputs:
      - name: reviewed
        type: data
        schema: {type: boolean}
  - id: audit
    depends_on: [analyze]
    prompt: Confirm evidence is available.
    outputs:
      - name: available
        type: data
        schema: {type: boolean}
""")
            with patch.object(
                TreeSitterSyntaxParser,
                "parse",
                autospec=True,
                side_effect=TreeSitterSyntaxParser.parse,
            ) as parse:
                started = driver.start(
                    params={
                        "source": FileAnalysisSource(path=path).model_dump(mode="json")
                    }
                )
                self.assertIsNone(started.error, started.error)
                self.assertEqual(
                    [step.step_id for step in started.steps], ["classify", "audit"]
                )
                self.assertEqual(parse.call_count, 1)
                path.write_text("struct Changed {}", encoding="utf-8")
                pending = driver.advance(
                    {
                        "inspection-facts": {
                            "inspection-facts": {
                                "classify": {"reviewed": True},
                            }
                        }
                    }
                )
                self.assertEqual([step.step_id for step in pending.steps], ["audit"])
                finished = driver.advance(
                    {
                        "inspection-facts": {
                            "inspection-facts": {
                                "audit": {"available": True},
                            }
                        }
                    }
                )
                self.assertEqual(finished.status, "done", finished.error)
                self.assertEqual(parse.call_count, 1)

            records = EventParser().parse(
                (root / "runs" / started.run_id / "events.jsonl")
                .read_text()
                .splitlines()
            )
            completed = [
                StepCompletedEvent.model_validate(record)
                for record in records
                if record.get("event") == "step_completed"
            ]
            self.assertEqual(
                [event.step_id for event in completed], ["analyze", "classify", "audit"]
            )
            analysis = (
                OperationResult[SourceAnalysis]
                .model_validate(completed[0].outputs)
                .result
            )
            self.assertEqual(analysis.source_identity, str(path))
            self.assertEqual(
                [fact.expression for fact in analysis.type_inspections],
                [
                    "value as? Model",
                    "is Model",
                    "as Failure",
                ],
            )
            self.assertEqual(
                [fact.kind.value for fact in analysis.type_inspections],
                [
                    "conditional_cast",
                    "pattern_type_test",
                    "pattern_cast",
                ],
            )
            self.assertEqual(
                [fact.operand for fact in analysis.type_inspections],
                ["value", None, None],
            )
