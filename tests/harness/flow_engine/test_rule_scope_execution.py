"""Tests file- and unit-scoped rule materialization in one review."""

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.runs_base_dir_resolver import RunsBaseDirResolver


"""
solid-name: TestRuleScopeExecution
solid-category: integration-test
solid-spec: [SPEC-039]
solid-description: Proves file rules materialize once per file while unit rules materialize once per normalized unit.
"""
class TestRuleScopeExecution(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project_root = Path(temporary.name)
        self.workflow_root = self.project_root / "workflows" / "review"
        self.workflow_path = self._write_workflows()
        self.engine = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.project_root
            ),
            plugin_root=self.project_root,
        ).build()

    def test_materializes_file_rule_once_and_unit_rule_for_every_unit(self) -> None:
        started = self.engine.flow_start(str(self.workflow_path))
        expanded = self.engine.flow_next({
            started.steps[0].instance_id: {
                "review_file": {"source_identity": "Mixed.swift"},
                "units": [
                    {"name": "First"},
                    {"name": "Second"},
                ],
            }
        })

        self.assertIsNone(expanded.error, expanded.error)
        prompts = [step.prompt for step in expanded.steps]
        self.assertEqual(len(prompts), 6)
        self.assertEqual(
            len([prompt for prompt in prompts if "File Mixed.swift" in prompt]),
            2,
        )
        self.assertEqual(
            len([prompt for prompt in prompts if "Unit First" in prompt]),
            2,
        )
        self.assertEqual(
            len([prompt for prompt in prompts if "Unit Second" in prompt]),
            2,
        )

    def _write_workflows(self) -> Path:
        self._write_rule(
            workflow_id="file-rule",
            scope="file",
            prompt="File {{params.review_file.source_identity}}",
        )
        self._write_rule(
            workflow_id="unit-rule",
            scope="unit",
            prompt="Unit {{params.review_unit.name}}",
        )
        return self._write(
            "composite/workflow.yaml",
            """
            id: scope-review
            name: Scope Review
            max_turns: 10
            steps:
              - id: prepare
                prompt: Prepare the normalized file.
                outputs:
                  - name: review_file
                    type: data
                    schema: {type: object}
                  - name: units
                    type: data
                    schema:
                      type: array
                      items: {type: object}
              - include:
                  rules: all
                as: rules
                depends_on: [prepare]
                for_each: "{{steps.prepare.outputs.units}}"
                with:
                  review_file: "{{steps.prepare.outputs.review_file}}"
                  review_unit: "{{item}}"
            """,
        )

    def _write_rule(self, workflow_id: str, scope: str, prompt: str) -> None:
        self._write(
            f"{workflow_id}/workflow.yaml",
            f"""
            id: {workflow_id}
            name: {workflow_id}
            max_turns: 5
            rule:
              scope: {scope}
            steps:
              - id: measure
                type: metric
                metric_id: {workflow_id.upper()}-1
                prompt: "{prompt} metric"
                value: {{type: boolean}}
                scoring:
                  severe: {{operator: equals, value: true}}
              - id: classify_exception
                type: exception
                prompt: "{prompt} exception"
            """,
        )

    def _write(self, relative_path: str, content: str) -> Path:
        destination = self.workflow_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(textwrap.dedent(content), encoding="utf-8")
        return destination


if __name__ == "__main__":
    unittest.main()
