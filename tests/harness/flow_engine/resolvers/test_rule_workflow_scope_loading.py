"""Tests typed rule execution scope through catalog expansion."""

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_engine_assembly_factory import FlowEngineAssemblyFactory
from harness.models import FlowValidationError
from harness.rule_scope import RuleScope


"""
solid-name: TestRuleWorkflowScopeLoading
solid-category: unit-test
solid-spec: [SPEC-039]
solid-description: Validates typed rule scope defaults, file-scope parsing, and scope-preserving all-rules expansion.
"""
class TestRuleWorkflowScopeLoading(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.loader = FlowEngineAssemblyFactory().build().flow_loader

    def test_defaults_an_ordinary_rule_to_unit_scope(self) -> None:
        path = self._write_rule("unit-default", "")

        flow = self.loader.load(str(path), [str(self.root)])

        self.assertEqual(flow.rule.scope, RuleScope.UNIT)

    def test_preserves_file_and_unit_scope_through_all_rules_expansion(self) -> None:
        self._write_rule("file-rule", "scope: file")
        self._write_rule("unit-rule", "scope: unit")
        composite = self._write(
            "review/workflow.yaml",
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

        flow = self.loader.load(str(composite), [str(self.root)])
        groups = {
            group.rule_workflow.workflow_id: group
            for group in flow.alias_groups
            if group.rule_workflow is not None
        }

        self.assertEqual(
            groups["file-rule"].rule_workflow.declaration.scope,
            RuleScope.FILE,
        )
        self.assertIsNone(groups["file-rule"].for_each)
        self.assertEqual(
            groups["unit-rule"].rule_workflow.declaration.scope,
            RuleScope.UNIT,
        )
        self.assertIsNotNone(groups["unit-rule"].for_each)

    def test_rejects_an_unknown_rule_scope(self) -> None:
        path = self._write_rule("invalid-scope", "scope: project")

        with self.assertRaises(FlowValidationError):
            self.loader.load(str(path), [str(self.root)])

    def _write_rule(self, workflow_id: str, scope: str) -> Path:
        rule_declaration = f"\n              {scope}" if scope else "{}"
        return self._write(
            f"{workflow_id}/workflow.yaml",
            f"""
            id: {workflow_id}
            name: {workflow_id}
            max_turns: 5
            rule: {rule_declaration}
            steps:
              - id: measure
                type: metric
                metric_id: {workflow_id.upper()}-1
                prompt: Measure the source.
                value: {{type: boolean}}
                scoring:
                  severe: {{operator: equals, value: true}}
              - id: classify_exception
                type: exception
                prompt: Classify the exception.
            """,
        )

    def _write(self, relative_path: str, content: str) -> Path:
        destination = self.root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(textwrap.dedent(content), encoding="utf-8")
        return destination


if __name__ == "__main__":
    unittest.main()
