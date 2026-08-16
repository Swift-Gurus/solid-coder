"""
solid-name: test_output_schema_prompt_annotator
solid-category: unit-test
solid-spec: [SPEC-027]
solid-description: Tests folding a step's declared output schemas into its prompt text.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.output_schema_description_collector import OutputSchemaDescriptionCollector
from harness.output_schema_prompt_annotator import OutputSchemaPromptAnnotator
from harness.output_spec import OutputSpec
from harness.step_declaration import StepDeclaration
from harness.step_prompt_augmenter import StepPromptAugmenter
from json_serializer import JsonSerializer


class TestOutputSchemaPromptAnnotator(unittest.TestCase):

    def setUp(self):
        self.sut = OutputSchemaPromptAnnotator(
            description_collector=OutputSchemaDescriptionCollector(JsonSerializer()),
            prompt_augmenter=StepPromptAugmenter(),
        )

    def test_appends_the_full_schema_to_the_prompt(self):
        step = StepDeclaration(
            id="a",
            prompt="Produce a short greeting.",
            outputs=[
                OutputSpec(
                    name="greeting",
                    type="data",
                    schema={"type": "string"},
                )
            ],
        )

        resolved = self.sut.annotate(step)

        self.assertEqual(
            resolved.prompt,
            "Produce a short greeting.\n\n"
            "Return only one JSON object matching this schema. Do not wrap it in "
            "Markdown fences or include any other text: "
            "{\"type\": \"object\", \"properties\": {\"greeting\": "
            "{\"type\": \"string\"}}, \"required\": [\"greeting\"], "
            "\"additionalProperties\": false}",
        )

    def test_appends_one_response_schema_for_all_outputs(self):
        step = StepDeclaration(
            id="a",
            prompt="Do the thing.",
            outputs=[
                OutputSpec(name="a_out", type="data", schema={"type": "string"}),
                OutputSpec(name="b_out", type="data", schema={"type": "integer"}),
            ],
        )

        resolved = self.sut.annotate(step)

        self.assertEqual(
            resolved.prompt,
            "Do the thing.\n\n"
            "Return only one JSON object matching this schema. Do not wrap it in "
            "Markdown fences or include any other text: "
            "{\"type\": \"object\", \"properties\": {\"a_out\": "
            "{\"type\": \"string\"}, \"b_out\": {\"type\": \"integer\"}}, "
            "\"required\": [\"a_out\", \"b_out\"], \"additionalProperties\": false}",
        )

    def test_appends_declared_response_schema_to_session_delegate_prompt(self):
        step = StepDeclaration(
            id="delegate",
            type="delegate",
            mode="session",
            prompt="Drive the child workflow.",
            outputs=[
                OutputSpec(
                    name="child_value",
                    type="data",
                    schema={"type": "integer"},
                )
            ],
        )

        resolved = self.sut.annotate(step)

        self.assertEqual(
            resolved.prompt,
            "Drive the child workflow.\n\n"
            "Return only one JSON object matching this schema. Do not wrap it in "
            "Markdown fences or include any other text: "
            "{\"type\": \"object\", \"properties\": {\"child_value\": "
            "{\"type\": \"integer\"}}, \"required\": [\"child_value\"], "
            "\"additionalProperties\": false}",
        )

    def test_names_declared_outputs_without_a_value_schema(self):
        step = StepDeclaration(
            id="a",
            prompt="Do the thing.",
            outputs=[OutputSpec(name="a_out", type="file")],
        )

        resolved = self.sut.annotate(step)

        self.assertEqual(
            resolved.prompt,
            "Do the thing.\n\n"
            "Return only one JSON object matching this schema. Do not wrap it in "
            "Markdown fences or include any other text: "
            "{\"type\": \"object\", \"properties\": {\"a_out\": {}}, "
            "\"required\": [\"a_out\"], \"additionalProperties\": false}",
        )

    def test_leaves_step_unchanged_when_no_outputs_declared(self):
        step = StepDeclaration(id="a", prompt="Do the thing.")

        resolved = self.sut.annotate(step)

        self.assertEqual(resolved, step)

    def test_is_idempotent_when_run_on_an_already_annotated_step(self):
        step = StepDeclaration(
            id="a",
            prompt="Produce a short greeting.",
            outputs=[
                OutputSpec(
                    name="greeting",
                    type="data",
                    schema={"type": "string"},
                )
            ],
        )

        once = self.sut.annotate(step)
        twice = self.sut.annotate(once)

        self.assertEqual(once.prompt, twice.prompt)

    def test_leaves_script_step_unchanged_even_with_schema_outputs(self):
        step = StepDeclaration(
            id="a",
            type="script",
            command=["python3", "run.py"],
            outputs=[
                OutputSpec(name="a_out", type="data", schema={"type": "string"})
            ],
        )

        resolved = self.sut.annotate(step)

        self.assertEqual(resolved, step)

    def test_leaves_command_step_unchanged_even_with_schema_outputs(self):
        step = StepDeclaration(
            id="a",
            type="command",
            command="printf '{\"ok\": true}'",
            outputs=[
                OutputSpec(name="ok", type="data", schema={"type": "boolean"})
            ],
        )

        resolved = self.sut.annotate(step)

        self.assertEqual(resolved, step)


if __name__ == "__main__":
    unittest.main()
