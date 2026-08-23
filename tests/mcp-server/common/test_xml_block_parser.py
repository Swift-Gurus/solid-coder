"""Verifies authored rule tags are distinguished from inline references."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_MCP_SERVER = Path(__file__).resolve().parents[3] / "mcp-server"
if str(_MCP_SERVER) not in sys.path:
    sys.path.insert(0, str(_MCP_SERVER))

from common.xml_block_parser import parse  # noqa: E402


class TestXmlBlockParser(unittest.TestCase):

    def test_inline_exception_reference_is_not_an_opening_block(self) -> None:
        content = """
<detection id="OCP-1">
Apply only the `<exceptions principle="OCP">` block below.
</detection>

<exceptions>
Pure data structures are exempt.
</exceptions>
"""

        parsed = parse(content)

        self.assertEqual(
            parsed["exceptions"],
            "Pure data structures are exempt.",
        )


if __name__ == "__main__":
    unittest.main()
