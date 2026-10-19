"""Exercises include conditions in their declaring scope, not the child scope."""

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "mcp-server"))

from harness.event_replayer import EventParser
from operation_workflow_integration_driver import OperationWorkflowIntegrationDriver


"""
solid-name: TestNestedIncludeConditionScope
solid-category: integration-test
solid-spec: [SPEC-037, SPEC-064]
solid-description: Proves nested include conditions read the owning workflow's outputs and parameters while child step conditions use child inputs, with durable skips and replay.
"""
class TestNestedIncludeConditionScope(TestCase):
    def test_parent_conditions_and_child_conditions_keep_distinct_scopes(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            driver = OperationWorkflowIntegrationDriver(root, [])
            driver.workflow_path = root / "root.yaml"
            (root / "leaf.yaml").write_text('''
name: Leaf
steps:
  - id: inspect
    when: {ref: "{{params.enabled}}", equals: false}
    prompt: Inspect with child enabled={{params.enabled}}
''')
            (root / "middle.yaml").write_text('''
name: Middle
steps:
  - id: decide
    prompt: Decide for parent enabled={{params.enabled}}
    outputs:
      - {name: allowed, type: data, schema: {type: boolean}}
      - name: targets
        type: data
        schema: {type: array, items: {type: object}}
  - include: leaf.yaml
    as: leaves
    depends_on: [decide]
    for_each: "{{steps.decide.outputs.targets}}"
    when:
      all:
        - {ref: "{{steps.decide.outputs.allowed}}", equals: true}
        - {ref: "{{params.enabled}}", equals: true}
        - {ref: "{{item.selected}}", equals: true}
    with:
      enabled: "{{params.child_enabled}}"
''')
            driver.write_workflow('''
name: Nested condition scopes
max_turns: 10
steps:
  - id: prepare
    prompt: Prepare parents
    outputs:
      - name: parents
        type: data
        schema: {type: array, items: {type: object}}
  - include: middle.yaml
    as: parents
    depends_on: [prepare]
    for_each: "{{steps.prepare.outputs.parents}}"
    with:
      enabled: "{{item.enabled}}"
      child_enabled: "{{params.child_enabled}}"
''')
            started = driver.start(params={"child_enabled": False})
            self.assertIsNone(started.error, started.error)
            parents = driver.advance({started.steps[0].instance_id: {
                "parents": [{"enabled": True}, {"enabled": False}],
            }})
            self.assertIsNone(parents.error, parents.error)
            self.assertEqual(len(parents.steps), 2)
            leaves = driver.advance({step.instance_id: {
                "allowed": True,
                "targets": [{"selected": True}, {"selected": False}],
            } for step in parents.steps})
            self.assertIsNone(leaves.error, leaves.error)
            self.assertEqual(len(leaves.steps), 1)
            self.assertIn("Inspect with child enabled=False", leaves.steps[0].prompt)
            replayed = driver.advance()
            self.assertEqual([step.instance_id for step in replayed.steps],
                             [step.instance_id for step in leaves.steps])
            finished = driver.advance({leaves.steps[0].instance_id: {}})
            self.assertIsNone(finished.error, finished.error)
            self.assertEqual(finished.status, "done")
            events = EventParser().parse((root / "runs" / started.run_id / "events.jsonl").read_text().splitlines())
            skips = [event for event in events if event.get("event") == "step_skipped"]
            self.assertEqual(len(skips), 3)
            self.assertTrue(all(event["condition"]["all"][0]["ref"] == "{{steps.decide.outputs.allowed}}" for event in skips))
