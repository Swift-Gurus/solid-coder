"""
solid-name: test_step_handler_resolver
solid-category: unit-test
solid-spec: [SPEC-027]
solid-description: Tests resolving the registered StepHandling implementation for a step's declared type.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.step_handler_resolver import StepHandlerResolver


class TestStepHandlerResolver(unittest.TestCase):

    def test_resolves_registered_handler_by_type(self):
        agent_handler = object()
        script_handler = object()
        sut = StepHandlerResolver(handlers={"agent": agent_handler, "script": script_handler})

        self.assertIs(sut.resolve("agent"), agent_handler)
        self.assertIs(sut.resolve("script"), script_handler)

    def test_raises_for_unregistered_type(self):
        sut = StepHandlerResolver(handlers={"agent": object()})

        with self.assertRaises(ValueError):
            sut.resolve("unknown")


if __name__ == "__main__":
    unittest.main()
