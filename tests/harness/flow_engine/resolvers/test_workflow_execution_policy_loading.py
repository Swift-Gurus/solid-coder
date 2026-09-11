"""Tests typed loading and lexical scoping of workflow execution policy."""

from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_engine_assembly_factory import FlowEngineAssemblyFactory
from harness.flow_validation_error import FlowValidationError
from harness.workflow_execution_mode import WorkflowExecutionMode
from harness.workflow_persister_factory import make_workflow_persister
from harness.workflow_presentation_mode import WorkflowPresentationMode


"""
solid-name: TestWorkflowExecutionPolicyLoading
solid-category: unit-test
solid-spec: [SPEC-045]
solid-description: Proves aggregate execution and combined presentation retain explicit lexical ownership through loading and include expansion.
"""
class TestWorkflowExecutionPolicyLoading(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.loader = FlowEngineAssemblyFactory().build().flow_loader

    def test_omitted_policy_retains_granular_individual_defaults(self) -> None:
        workflow = self._write(
            "plain.yaml",
            """
            id: plain
            steps:
              - id: inspect
                prompt: Inspect.
            """,
        )

        loaded = self.loader.load(str(workflow), [])

        self.assertIs(loaded.execution, WorkflowExecutionMode.GRANULAR)
        self.assertIs(loaded.presentation, WorkflowPresentationMode.INDIVIDUAL)

    def test_loads_typed_workflow_root_policy(self) -> None:
        workflow = self._write(
            "aggregate.yaml",
            """
            id: aggregate
            execution:
              mode: aggregate
            presentation:
              mode: combined
            steps:
              - id: inspect
                prompt: Inspect.
            """,
        )

        loaded = self.loader.load(str(workflow), [])

        self.assertIs(loaded.execution, WorkflowExecutionMode.AGGREGATE)
        self.assertIs(loaded.presentation, WorkflowPresentationMode.COMBINED)

    def test_rejects_unknown_execution_mode(self) -> None:
        workflow = self._write(
            "invalid.yaml",
            """
            id: invalid
            execution:
              mode: invented
            steps:
              - id: inspect
                prompt: Inspect.
            """,
        )

        with self.assertRaisesRegex(FlowValidationError, "execution"):
            self.loader.load(str(workflow), [])

    def test_inline_group_policy_is_owned_by_that_group(self) -> None:
        workflow = self._write(
            "inline.yaml",
            """
            id: inline
            steps:
              - group: selected
                execution:
                  mode: aggregate
                presentation:
                  mode: combined
                steps:
                  - id: inspect
                    prompt: Inspect.
            """,
        )

        loaded = self.loader.load(str(workflow), [])
        group = next(group for group in loaded.alias_groups if group.alias == "selected")

        self.assertIs(group.execution, WorkflowExecutionMode.AGGREGATE)
        self.assertIs(group.presentation, WorkflowPresentationMode.COMBINED)

    def test_child_root_policy_survives_parent_without_policy(self) -> None:
        self._write(
            "child.yaml",
            """
            id: child
            execution:
              mode: aggregate
            presentation:
              mode: combined
            steps:
              - id: inspect
                prompt: Inspect.
            """,
        )
        parent = self._write(
            "parent.yaml",
            """
            id: parent
            steps:
              - include: child.yaml
                as: child
              - id: sibling
                prompt: Remain granular.
            """,
        )

        loaded = self.loader.load(str(parent), [])
        child = next(group for group in loaded.alias_groups if group.alias == "child")

        self.assertIs(loaded.execution, WorkflowExecutionMode.GRANULAR)
        self.assertIs(loaded.presentation, WorkflowPresentationMode.INDIVIDUAL)
        self.assertIs(child.execution, WorkflowExecutionMode.AGGREGATE)
        self.assertIs(child.presentation, WorkflowPresentationMode.COMBINED)

    def test_explicit_enclosing_policy_does_not_rewrite_nested_policy(self) -> None:
        self._write(
            "child.yaml",
            """
            id: child
            execution:
              mode: aggregate
            steps:
              - group: inner
                presentation:
                  mode: combined
                steps:
                  - id: inspect
                    prompt: Inspect.
            """,
        )
        parent = self._write(
            "parent.yaml",
            """
            id: parent
            presentation:
              mode: combined
            steps:
              - include: child.yaml
                as: child
            """,
        )

        loaded = self.loader.load(str(parent), [])
        child = next(group for group in loaded.alias_groups if group.alias == "child")
        inner = next(group for group in loaded.alias_groups if group.alias == "child.inner")

        self.assertIs(child.execution, WorkflowExecutionMode.AGGREGATE)
        self.assertIs(child.presentation, WorkflowPresentationMode.INDIVIDUAL)
        self.assertIs(inner.execution, WorkflowExecutionMode.GRANULAR)
        self.assertIs(inner.presentation, WorkflowPresentationMode.COMBINED)

    def test_catalog_include_preserves_child_root_policy(self) -> None:
        package = self.root / "workflows" / "catalog-child"
        package.mkdir(parents=True)
        (package / "workflow.yaml").write_text(
            textwrap.dedent(
                """
                id: catalog-child
                name: Catalog Child
                max_turns: 5
                execution:
                  mode: aggregate
                presentation:
                  mode: combined
                steps:
                  - id: inspect
                    prompt: Inspect.
                """
            ),
            encoding="utf-8",
        )
        parent = self._write(
            "parent.yaml",
            """
            id: parent
            steps:
              - include:
                  workflow: catalog-child
                as: child
            """,
        )

        loaded = self.loader.load(str(parent), [str(self.root / "workflows")])
        child = next(group for group in loaded.alias_groups if group.alias == "child")

        self.assertIs(child.execution, WorkflowExecutionMode.AGGREGATE)
        self.assertIs(child.presentation, WorkflowPresentationMode.COMBINED)

    def test_snapshot_reload_preserves_root_and_nested_policy(self) -> None:
        workflow = self._write(
            "snapshot-source.yaml",
            """
            id: snapshot-source
            execution:
              mode: aggregate
            steps:
              - group: selected
                presentation:
                  mode: combined
                steps:
                  - id: inspect
                    prompt: Inspect.
            """,
        )
        loaded = self.loader.load(str(workflow), [])
        run_directory = self.root / "run"
        run_directory.mkdir()
        make_workflow_persister().persist(run_directory, loaded)

        restored = self.loader.load(str(run_directory / "workflow.yaml"), [])
        group = next(group for group in restored.alias_groups if group.alias == "selected")

        self.assertIs(restored.execution, WorkflowExecutionMode.AGGREGATE)
        self.assertIs(restored.presentation, WorkflowPresentationMode.INDIVIDUAL)
        self.assertIs(group.execution, WorkflowExecutionMode.GRANULAR)
        self.assertIs(group.presentation, WorkflowPresentationMode.COMBINED)

    def _write(self, name: str, content: str) -> Path:
        path = self.root / name
        path.write_text(textwrap.dedent(content), encoding="utf-8")
        return path


if __name__ == "__main__":
    unittest.main()
