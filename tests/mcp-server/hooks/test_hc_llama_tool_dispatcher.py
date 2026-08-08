"""
solid-description: Verify tool dispatcher correctly processes tool invocations and handles errors appropriately.
solid-category: unit-test
"""

import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks", Path(__file__).resolve().parent)

from hc_llama_runner import GatewayToolDispatcher  # noqa: E402
from hc_rule_loader import GatewayFixInvoker  # noqa: E402
from llama.codebase_searcher import CodebaseSearcher  # noqa: E402
from llama.tool_call_parser import ToolCallParser  # noqa: E402

_SEARCH      = "mcp__pipeline__search_codebase"
_READ        = "mcp__pipeline__read_file"
_GREP        = "mcp__pipeline__grep_codebase"
_GLOB        = "mcp__pipeline__glob_codebase"
_FIX         = "mcp__docs__load_fix_for_violation"
_SUBMIT      = "mcp__pipeline__submit_batch_findings"
_SUBMIT_FIX  = "mcp__pipeline__submit_fix"


def _tc(name: str, args: dict, call_id: str = "c1") -> dict:
    return {"id": call_id, "type": "function",
            "function": {"name": name, "arguments": json.dumps(args)}}


class TestGatewayToolDispatcher(unittest.TestCase):
    def _make(self, return_value=None):
        invoker = MagicMock()
        invoker.invoke.return_value = return_value
        grep_fn = MagicMock(return_value="")
        glob_fn = MagicMock(return_value="")
        search_fn = MagicMock(return_value="")
        read_fn = MagicMock(return_value="")
        fns = {"grep_fn": grep_fn, "glob_fn": glob_fn, "search_fn": search_fn, "read_fn": read_fn}
        searcher = CodebaseSearcher(
            search_fn=search_fn, grep_fn=grep_fn, glob_fn=glob_fn, read_fn=read_fn,
        )
        d = GatewayToolDispatcher(
            codebase_search=searcher,
            fix_invoker=GatewayFixInvoker(invoker=invoker),
            parser=ToolCallParser(),
        )
        return d, invoker, fns

    def _extra_args(self, invoker) -> list:
        call = invoker.invoke.call_args
        return call[1].get("extra_args") or call[0][1]

    def test_search_codebase_delegates_to_search_fn(self):
        d, _, fns = self._make()
        fns["search_fn"].return_value = "tests/Foo.swift — Foo service"
        result = d.dispatch(_tc(_SEARCH, {
            "query": "Foo service repository",
            "output_dir": "/health/run",
        }))
        fns["search_fn"].assert_called_once_with("Foo service repository", "/health/run")
        self.assertEqual(result, "tests/Foo.swift — Foo service")

    def test_read_file_delegates_to_read_fn(self):
        d, _, fns = self._make()
        fns["read_fn"].return_value = "class Foo {}"
        result = d.dispatch(_tc(_READ, {"file_path": "/src/Foo.swift"}))
        fns["read_fn"].assert_called_once_with("/src/Foo.swift")
        self.assertEqual(result, "class Foo {}")

    def test_read_file_does_not_use_invoker(self):
        d, invoker, _ = self._make()
        d.dispatch(_tc(_READ, {"file_path": "/src/Foo.swift"}))
        invoker.invoke.assert_not_called()

    def test_search_codebase_does_not_use_invoker(self):
        d, invoker, _ = self._make()
        d.dispatch(_tc(_SEARCH, {"query": "Foo", "output_dir": "/health/run"}))
        invoker.invoke.assert_not_called()

    def test_load_fix_invokes_correct_subcommand(self):
        d, invoker, _ = self._make({"content": "fix"})
        d.dispatch(_tc(_FIX, {"metric_id": "OCP-1"}))
        self.assertEqual(invoker.invoke.call_args[0][0], "load_fix_for_violation")

    def test_load_fix_passes_metric_id_in_extra_args(self):
        d, invoker, _ = self._make({"content": "fix"})
        d.dispatch(_tc(_FIX, {"metric_id": "OCP-1"}))
        self.assertIn("OCP-1", self._extra_args(invoker))

    def test_load_fix_uses_metric_ids_plural_flag(self):
        d, invoker, _ = self._make({"content": "fix"})
        d.dispatch(_tc(_FIX, {"metric_id": "OCP-1"}))
        self.assertIn("--metric_ids", self._extra_args(invoker))

    def test_unknown_tool_returns_error_string(self):
        d, _, _ = self._make()
        self.assertIn("unknown tool", d.dispatch(_tc("nonexistent", {})))

    def test_malformed_arguments_falls_back_to_empty_args(self):
        d, _, _ = self._make(None)
        tc = {"id": "x", "function": {"name": _SEARCH, "arguments": "not json"}}
        self.assertIsInstance(d.dispatch(tc), str)

    def test_arguments_as_dict_handled_gracefully(self):
        d, _, fns = self._make()
        tc = {"id": "x", "function": {"name": _SEARCH, "arguments": {
            "query": "Foo",
            "output_dir": "/health/run",
        }}}
        d.dispatch(tc)
        fns["search_fn"].assert_called_once_with("Foo", "/health/run")

    def test_search_returns_fn_result_directly(self):
        d, _, fns = self._make()
        fns["search_fn"].return_value = "tests/Foo.swift — Foo type"
        self.assertEqual(
            d.dispatch(_tc(_SEARCH, {"query": "Foo", "output_dir": "/health/run"})),
            "tests/Foo.swift — Foo type",
        )

    def test_search_returns_empty_string_when_fn_returns_empty(self):
        d, _, fns = self._make()
        fns["search_fn"].return_value = ""
        self.assertEqual(
            d.dispatch(_tc(_SEARCH, {"query": "Foo", "output_dir": "/health/run"})),
            "",
        )

    def test_search_schema_requires_output_directory(self):
        from llama.tool_dispatcher import TOOLS
        search_tool = next(
            tool for tool in TOOLS
            if tool["function"]["name"] == "mcp__pipeline__search_codebase"
        )

        self.assertEqual(
            search_tool["function"]["parameters"]["required"],
            ["query", "output_dir"],
        )

    def test_load_fix_returns_content_string_not_json_encoded_dict(self):
        fix_content = "<fix>\nIntroduce a protocol.\n</fix>"
        d, _, _ = self._make(fix_content)
        result = d.dispatch(_tc(_FIX, {"metric_id": "OCP-1"}))
        self.assertEqual(result, fix_content)
        self.assertNotIn("\\n", result)
        self.assertNotIn('\\"', result)

    def test_load_fix_returns_empty_string_on_invoker_failure(self):
        d, _, _ = self._make(None)
        self.assertEqual(d.dispatch(_tc(_FIX, {"metric_id": "OCP-1"})), "")

    def test_grep_codebase_delegates_to_grep_fn(self):
        d, _, fns = self._make()
        fns["grep_fn"].return_value = "/src/Foo.swift:1: class Foo"
        result = d.dispatch(_tc(_GREP, {"name": "Foo"}))
        fns["grep_fn"].assert_called_once_with("Foo")
        self.assertEqual(result, "/src/Foo.swift:1: class Foo")

    def test_glob_codebase_delegates_to_glob_fn(self):
        d, _, fns = self._make()
        fns["glob_fn"].return_value = "/src/FooManager.swift"
        result = d.dispatch(_tc(_GLOB, {"pattern": "*Foo*"}))
        fns["glob_fn"].assert_called_once_with("*Foo*")
        self.assertEqual(result, "/src/FooManager.swift")

    def test_submit_fix_invokes_correct_subcommand(self):
        fixes = [{"rule_id": "SRP-1", "file_path": "/p.swift", "unit_name": "Foo", "suggested_fix": "Extract."}]
        d, invoker, _ = self._make("{}")
        d.dispatch(_tc(_SUBMIT_FIX, {"output_dir": "/out", "fixes": fixes}))
        self.assertEqual(invoker.invoke.call_args[0][0], "submit_fix")

    def test_submit_fix_passes_output_dir(self):
        fixes = [{"rule_id": "SRP-1", "file_path": "/p.swift", "unit_name": "Foo", "suggested_fix": "Extract."}]
        d, invoker, _ = self._make("{}")
        d.dispatch(_tc(_SUBMIT_FIX, {"output_dir": "/my/out", "fixes": fixes}))
        self.assertIn("--output_dir", self._extra_args(invoker))
        self.assertIn("/my/out", self._extra_args(invoker))

    def test_submit_fix_is_in_tools_list(self):
        from llama.tool_dispatcher import TOOLS
        names = [t["function"]["name"] for t in TOOLS]
        self.assertIn("mcp__pipeline__submit_fix", names)


if __name__ == "__main__":
    unittest.main()
