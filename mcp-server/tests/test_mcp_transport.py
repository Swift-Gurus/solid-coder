"""Tests for MCPServer tool registration with _meta support."""

import sys
import unittest
from pathlib import Path

MCP_DIR = str(Path(__file__).resolve().parents[1])
if MCP_DIR not in sys.path:
    sys.path.insert(0, MCP_DIR)

from mcp_server_factory import MCPServerFactory


def _server_with_tool(meta=None):
    s = MCPServerFactory().build("test", "1.0.0")
    kwargs = dict(
        name="my_tool",
        description="test",
        input_schema={"type": "object", "properties": {}},
    )
    if meta is not None:
        kwargs["meta"] = meta

    @s.tool(**kwargs)
    def handler():
        return "ok"

    return s


def _list_tools(server):
    response = server._transport_runner._dispatcher.dispatch("tools/list", 1, {})
    return {t["name"]: t for t in response["result"]["tools"]}


class TestToolMetaRegistration(unittest.TestCase):
    def test_tool_without_meta_has_no_meta_field(self):
        s = _server_with_tool()
        self.assertNotIn("_meta", _list_tools(s)["my_tool"])

    def test_tool_with_meta_stores_meta_under_meta_key(self):
        s = _server_with_tool(meta={"anthropic/maxResultSizeChars": 200000})
        tool = _list_tools(s)["my_tool"]
        self.assertIn("_meta", tool)
        self.assertEqual(tool["_meta"]["anthropic/maxResultSizeChars"], 200000)

    def test_tools_list_payload_carries_meta(self):
        """The tools/list RPC payload must include _meta."""
        s = _server_with_tool(meta={"anthropic/maxResultSizeChars": 200000})
        tool = _list_tools(s)["my_tool"]
        self.assertEqual(tool["_meta"]["anthropic/maxResultSizeChars"], 200000)


class TestLoadRulesAnnotation(unittest.TestCase):
    def test_load_rules_declares_max_result_size(self):
        """load_rules must carry anthropic/maxResultSizeChars so large rule sets
        are never silently persisted to disk and replaced with a file reference."""
        import docs.server as docs_server
        tool = _list_tools(docs_server.server).get("load_rules")
        self.assertIsNotNone(tool, "load_rules must be registered in docs server")
        self.assertIn("_meta", tool)
        self.assertGreater(tool["_meta"].get("anthropic/maxResultSizeChars", 0), 0)


class TestLoadSpecContextAnnotation(unittest.TestCase):
    def test_load_spec_context_declares_max_result_size(self):
        """load_spec_context must carry anthropic/maxResultSizeChars so large
        spec ancestor chains are never silently persisted to disk."""
        import specs.server as specs_server
        tool = _list_tools(specs_server.server).get("load_spec_context")
        self.assertIsNotNone(tool, "load_spec_context must be registered in specs server")
        self.assertIn("_meta", tool)
        self.assertGreater(tool["_meta"].get("anthropic/maxResultSizeChars", 0), 0)


if __name__ == "__main__":
    unittest.main()
