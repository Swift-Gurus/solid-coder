"""
solid-name: TestFlowLoader
solid-description: Validates the loading of flow configuration files and detection of structural errors.
solid-category: unit-test
"""

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.command_allowlist_resolver import CommandAllowlistResolver
from harness.command_allowlist_validator import CommandAllowlistValidator
from harness.flow_config_extractor import FlowConfigExtractor
from harness.flow_engine_assembly import build_default_assembly
from harness.flow_graph_validator import FlowGraphValidator
from harness.flow_loader import FlowLoader
from harness.for_each_reference_validator import ForEachReferenceValidator
from harness.group_dependency_expander import GroupDependencyExpander
from harness.include_resolver import IncludeResolver
from harness.include_structure_validator import IncludeStructureValidator
from harness.json_loading import JsonLoader
from harness.kahn_cycle_detector import KahnCycleDetector
from harness.models import FlowValidationError
from harness.output_schema_prompt_annotator import OutputSchemaPromptAnnotator
from harness.output_schema_resolver import OutputSchemaResolver
from harness.prompt_content_resolver import PromptContentResolver
from harness.step_builder import StepBuilder
from harness.step_graph_validator import StepGraphValidator
from harness.step_shape_validator import StepShapeValidator
from harness.uses_resolver import UsesResolver
from scoring.yaml_config_file_loader import YamlConfigFileLoader
from scoring.yaml_loader import PyYamlLoader
from utils.prompt_builder import PlainTextFileReader


def _make_graph_validator() -> FlowGraphValidator:
    cycle_detector = KahnCycleDetector()
    return FlowGraphValidator(
        step_graph_validator=StepGraphValidator(cycle_detector=cycle_detector),
        include_structure_validator=IncludeStructureValidator(cycle_detector=cycle_detector),
        for_each_validator=ForEachReferenceValidator(),
    )


def _loader_with_allowlist(allowlist: list[str]) -> FlowLoader:
    yaml_file_loader = YamlConfigFileLoader(loader=PyYamlLoader())
    json_file_loader = YamlConfigFileLoader(loader=JsonLoader())
    return FlowLoader(
        file_loader=yaml_file_loader,
        config_extractor=FlowConfigExtractor(),
        uses_resolver=UsesResolver(file_loader=yaml_file_loader),
        graph_validator=_make_graph_validator(),
        step_builder=StepBuilder(),
        include_resolver=IncludeResolver(file_loader=yaml_file_loader),
        step_shape_validator=StepShapeValidator(),
        prompt_content_resolver=PromptContentResolver(reader=PlainTextFileReader()),
        output_schema_resolver=OutputSchemaResolver(file_loader=json_file_loader),
        output_schema_prompt_annotator=OutputSchemaPromptAnnotator(),
        command_allowlist_resolver=CommandAllowlistResolver(section_reader=lambda name: {"permitted_executables": allowlist}),
        command_allowlist_validator=CommandAllowlistValidator(),
        group_dependency_expander=GroupDependencyExpander(),
    )


class TestFlowLoader(unittest.TestCase):

    def setUp(self):
        self.assembly = build_default_assembly()
        self.loader = self.assembly.flow_loader
        self._tmpdir = tempfile.mkdtemp()

    def _write(self, name: str, content: str) -> str:
        path = str(Path(self._tmpdir) / name)
        Path(path).write_text(textwrap.dedent(content))
        return path

    def test_loads_minimal_valid_flow(self):
        path = self._write("flow.yaml", """
            name: my_flow
            max_turns: 5
            steps:
              - id: step_a
                prompt: Do something
        """)
        flow = self.loader.load(path, [])
        self.assertEqual(flow.name, "my_flow")
        self.assertEqual(flow.max_turns, 5)
        self.assertEqual(len(flow.steps), 1)
        self.assertEqual(flow.steps[0].id, "step_a")

    def test_raises_on_missing_file(self):
        with self.assertRaises(FlowValidationError):
            self.loader.load("/nonexistent/flow.yaml", [])

    def test_raises_on_duplicate_step_ids(self):
        path = self._write("dupe.yaml", """
            name: dupe
            steps:
              - id: a
                prompt: First
              - id: a
                prompt: Second
        """)
        with self.assertRaises(FlowValidationError):
            self.loader.load(path, [])

    def test_raises_on_unknown_dependency(self):
        path = self._write("bad_dep.yaml", """
            name: bad
            steps:
              - id: a
                prompt: p
                depends_on: [nonexistent]
        """)
        with self.assertRaises(FlowValidationError):
            self.loader.load(path, [])

    def test_raises_on_dependency_cycle(self):
        path = self._write("cycle.yaml", """
            name: cyclic
            steps:
              - id: a
                prompt: p
                depends_on: [b]
              - id: b
                prompt: p
                depends_on: [a]
        """)
        with self.assertRaises(FlowValidationError):
            self.loader.load(path, [])

    def test_loads_a_script_step_with_permitted_command(self):
        path = self._write("script_flow.yaml", """
            name: with_script
            steps:
              - id: gate
                type: script
                command: [python3, run.py]
                timeout_seconds: 30
        """)
        flow = _loader_with_allowlist(["python3"]).load(path, [])

        self.assertEqual(flow.steps[0].type, "script")
        self.assertEqual(flow.steps[0].command, ["python3", "run.py"])

    def test_raises_when_script_command_not_on_allowlist(self):
        path = self._write("script_flow.yaml", """
            name: with_script
            steps:
              - id: gate
                type: script
                command: [curl, evil.example]
        """)
        with self.assertRaises(FlowValidationError):
            _loader_with_allowlist(["python3"]).load(path, [])

    def test_resolves_prompt_file_for_agent_step(self):
        self._write("prompt.md", "Rendered prompt text")
        path = self._write("prompt_file_flow.yaml", """
            name: with_prompt_file
            steps:
              - id: a
                prompt_file: prompt.md
        """)
        flow = self.loader.load(path, [])

        self.assertEqual(flow.steps[0].prompt, "Rendered prompt text")

    def test_resolves_schema_file_for_output_spec(self):
        self._write("greeting_schema.json", '{"type": "string"}')
        path = self._write("schema_file_flow.yaml", """
            name: with_schema_file
            steps:
              - id: a
                prompt: p
                outputs:
                  - name: greeting
                    type: data
                    schema_file: greeting_schema.json
        """)
        flow = self.loader.load(path, [])

        self.assertEqual(flow.steps[0].outputs[0].schema, {"type": "string"})

    def test_folds_output_schema_into_the_step_prompt(self):
        path = self._write("schema_prompt_flow.yaml", """
            name: with_schema_in_prompt
            steps:
              - id: a
                prompt: Produce a short greeting.
                outputs:
                  - name: greeting
                    type: data
                    schema:
                      type: string
        """)
        flow = self.loader.load(path, [])

        self.assertEqual(
            flow.steps[0].prompt,
            "Produce a short greeting.\n\n"
            "Submit output 'greeting' matching this schema: {\"type\": \"string\"}",
        )

    def test_loading_an_already_resolved_workflow_snapshot_does_not_double_the_folded_schema(self):
        # Mirrors YamlWorkflowPersister: the run engine persists the fully-resolved FlowDef (prompt
        # already schema-annotated, schema still present) to workflow.yaml, then reloads it on every
        # subsequent flow_next() call through this same loader — that reload must be a no-op.
        path = self._write("already_resolved_flow.yaml", """
            name: already_resolved
            steps:
              - id: a
                prompt: |-
                  Produce a short greeting.

                  Submit output 'greeting' matching this schema: {"type": "string"}
                outputs:
                  - name: greeting
                    type: data
                    schema:
                      type: string
        """)
        flow = self.loader.load(path, [])

        self.assertEqual(
            flow.steps[0].prompt,
            "Produce a short greeting.\n\n"
            "Submit output 'greeting' matching this schema: {\"type\": \"string\"}",
        )

    def test_raises_when_schema_file_missing(self):
        path = self._write("missing_schema_flow.yaml", """
            name: with_missing_schema_file
            steps:
              - id: a
                prompt: p
                outputs:
                  - name: greeting
                    type: data
                    schema_file: missing.json
        """)
        with self.assertRaises(FlowValidationError):
            self.loader.load(path, [])

    def test_loads_a_flow_with_an_aliased_include(self):
        self._write("sub.yaml", """
            steps:
              - id: step_a
                prompt: Do sub step
        """)
        path = self._write("parent.yaml", """
            name: parent
            steps:
              - include: sub.yaml
                as: sub
        """)
        flow = self.loader.load(path, [])

        self.assertEqual([s.id for s in flow.steps], ["sub.step_a"])

    def test_raises_when_include_alias_collides_with_existing_step_id(self):
        self._write("sub.yaml", """
            steps:
              - id: step_a
                prompt: p
        """)
        path = self._write("parent.yaml", """
            name: parent
            steps:
              - id: sub
                prompt: p
              - include: sub.yaml
                as: sub
        """)
        with self.assertRaises(FlowValidationError):
            self.loader.load(path, [])

    def test_loads_a_flow_with_an_inline_group_alongside_top_level_steps(self):
        path = self._write("inline_group.yaml", """
            name: inline_group
            steps:
              - id: setup
                prompt: p
              - group: review
                steps:
                  - id: draft
                    prompt: p
                    depends_on: [setup]
                  - id: approve
                    prompt: p
                    depends_on: [draft]
              - id: finish
                prompt: p
                depends_on: [review]
        """)
        flow = self.loader.load(path, [])

        self.assertEqual(flow.steps[0].id, "setup")
        self.assertEqual(flow.steps[-1].id, "finish")
        self.assertEqual(
            sorted(s.id for s in flow.steps), ["finish", "review.approve", "review.draft", "setup"]
        )
        self.assertEqual(sorted(flow.steps[-1].depends_on), ["review.approve", "review.draft"])

    def test_raises_when_inline_group_alias_collides_with_existing_step_id(self):
        path = self._write("inline_collision.yaml", """
            name: inline_collision
            steps:
              - id: review
                prompt: p
              - group: review
                steps:
                  - id: draft
                    prompt: p
        """)
        with self.assertRaises(FlowValidationError):
            self.loader.load(path, [])


if __name__ == "__main__":
    unittest.main()
