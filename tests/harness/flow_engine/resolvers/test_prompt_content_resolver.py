"""
solid-name: test_prompt_content_resolver
solid-category: unit-test
solid-spec: [SPEC-027]
solid-description: Tests resolving a step's prompt_file reference into inline prompt text relative to its flow file.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_validation_error import FlowValidationError
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.path_builder import PathBuilder
from harness.prompt_content_resolver import PromptContentResolver
from harness.prompt_file_loader import PromptFileLoader
from harness.prompt_file_path_resolver import PromptFilePathResolver
from harness.workflow_package_root_locator import WorkflowPackageRootLocator
from harness.workflow_resource_path_resolver import WorkflowResourcePathResolver


class StubTextFileReader:
    def __init__(self, contents: dict[str, str]) -> None:
        self._contents = contents

    def read(self, path: Path):
        return self._contents.get(str(path))


def _make_resolver(reader: StubTextFileReader) -> PromptContentResolver:
    error_factory = FlowValidationErrorFactory()
    resource_path_resolver = WorkflowResourcePathResolver(WorkflowPackageRootLocator())
    return PromptContentResolver(
        path_resolver=PromptFilePathResolver(PathBuilder(), resource_path_resolver),
        prompt_loader=PromptFileLoader(reader, error_factory),
    )


class TestPromptContentResolver(unittest.TestCase):

    def test_resolves_prompt_file_relative_to_flow_file(self):
        flow_path = "/flows/my_flow.yaml"
        prompt_path = str(Path("/flows/prompt.md"))
        reader = StubTextFileReader({prompt_path: "Do the thing"})
        sut = _make_resolver(reader)

        resolved = sut.resolve({"id": "step_a", "prompt_file": "prompt.md"}, flow_path)

        self.assertEqual(resolved["prompt"], "Do the thing")

    def test_removes_prompt_file_key_once_resolved_so_the_step_survives_a_round_trip(self):
        flow_path = "/flows/my_flow.yaml"
        prompt_path = str(Path("/flows/prompt.md"))
        reader = StubTextFileReader({prompt_path: "Do the thing"})
        sut = _make_resolver(reader)

        resolved = sut.resolve({"id": "step_a", "prompt_file": "prompt.md"}, flow_path)

        self.assertNotIn("prompt_file", resolved)

    def test_leaves_inline_prompt_unchanged_when_no_prompt_file(self):
        sut = _make_resolver(StubTextFileReader({}))
        step = {"id": "step_a", "prompt": "inline text"}

        resolved = sut.resolve(step, "/flows/my_flow.yaml")

        self.assertEqual(resolved["prompt"], "inline text")

    def test_raises_when_prompt_file_does_not_resolve(self):
        sut = _make_resolver(StubTextFileReader({}))

        with self.assertRaises(FlowValidationError) as ctx:
            sut.resolve({"id": "step_a", "prompt_file": "missing.md"}, "/flows/my_flow.yaml")

        self.assertIn("step_a", str(ctx.exception))
        self.assertIn("missing.md", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
