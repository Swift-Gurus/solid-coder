"""
solid-name: test_command_allowlist_resolver
solid-category: unit-test
solid-spec: [SPEC-027]
solid-description: Tests resolving the permitted-executable allowlist from the flow engine's config section.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.command_allowlist_resolver import CommandAllowlistResolver


class TestCommandAllowlistResolver(unittest.TestCase):

    def test_returns_permitted_executables_from_flow_engine_section(self):
        sut = CommandAllowlistResolver(
            section_reader=lambda name: {"permitted_executables": ["python3", "bash"]} if name == "flow_engine" else {}
        )

        self.assertEqual(sut.resolve(), ["python3", "bash"])

    def test_returns_empty_list_when_section_absent(self):
        sut = CommandAllowlistResolver(section_reader=lambda name: {})

        self.assertEqual(sut.resolve(), [])


if __name__ == "__main__":
    unittest.main()
