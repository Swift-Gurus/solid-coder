"""
solid-description: Dispatches tool calls to registered service handlers.
solid-category: service
solid-tags: [hook, llm]
"""

from typing import Optional, Protocol

from llama.codebase_searcher import CodebaseSearching  # noqa: F401
from llama.findings_submitter import FindingsSubmitting
from llama.tool_call_parser import ToolCallArgsParsing
from hc_rule_loader import FixInvoking  # noqa: F401


TOOLS: list = [
    {
        "type": "function",
        "function": {
            "name": "mcp__pipeline__search_codebase",
            "description": (
                "Search the codebase for existing implementations or similar types by semantic synonyms. "
                "Call with type name, camelCase-split words, and responsibility synonyms as the query."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Space-separated synonyms (name + camelCase words + responsibility keywords)"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mcp__pipeline__grep_codebase",
            "description": (
                "Search file contents for type definitions, extensions, and declarations of a given name. "
                "Finds: class/struct/protocol/enum/actor/extension/typealias <name>. "
                "Use for DRY Phase B — finding existing implementations by exact identifier."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Type or function name to search for (e.g. UserManager)"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mcp__pipeline__glob_codebase",
            "description": (
                "Search filenames matching a glob pattern. "
                "Example: '*UserManager*' finds all files whose name contains 'UserManager'. "
                "Complements grep: grep finds definitions inside files, glob finds files by name."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Glob pattern to match against filenames (e.g. *UserManager*)"},
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mcp__pipeline__read_file",
            "description": (
                "Read the full source code of a file by its absolute path. "
                "Use this after mcp__pipeline__search_codebase returns matches — for each matched "
                "file whose solid-description overlaps with the code under review, read the file "
                "to inspect its existing types, method signatures, and logic before deciding "
                "whether a DRY-1 reuse miss violation applies."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Absolute path of the file to read"},
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mcp__docs__load_fix_for_violation",
            "description": (
                "Load fix strategies for one or more metric IDs in a single call. "
                "Pass ALL violation metric_ids at once — all strategies are returned concatenated. "
                "Call ONCE with the full list to avoid per-violation round trips."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "metric_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "One or more metric IDs, e.g. ['SRP-2', 'OCP-1']. Pass all at once.",
                    },
                },
                "required": ["metric_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mcp__pipeline__submit_batch_findings",
            "description": (
                "Submit findings for all reviewed principles in one unified payload. "
                "Discovers principle keys from metrics, scores each, writes "
                "output_dir/{principle}/review-output.json."
            ),
            "parameters": {
                "type": "object",
                "required": ["output_dir", "submissions"],
                "properties": {
                    "output_dir": {"type": "string"},
                    "submissions": {
                        "type": "object",
                        "description": (
                            "Map of principle_name to review-output payload. "
                            "E.g. {'SRP': {timestamp, files:[{units:[{unit_name, unit_kind, "
                            "metrics:{SRP:{verb_count:{value:3}}}}]}]}}"
                        ),
                        "additionalProperties": {
                            "type": "object",
                            "required": ["timestamp", "files"],
                            "properties": {
                                "timestamp": {"type": "string"},
                                "files": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "required": ["units"],
                                        "properties": {
                                            "units": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "required": ["unit_name", "unit_kind", "metrics"],
                                                    "properties": {
                                                        "unit_name": {"type": "string"},
                                                        "unit_kind": {"type": "string"},
                                                        "metrics": {"type": "object"},
                                                    },
                                                },
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mcp__pipeline__submit_fix",
            "description": "Submit concrete fixes for ALL SEVERE violations in one call.",
            "parameters": {
                "type": "object",
                "required": ["output_dir", "fixes"],
                "properties": {
                    "output_dir": {"type": "string"},
                    "fixes": {
                        "type": "array",
                        "description": "One fix object per SEVERE violation.",
                        "items": {
                            "type": "object",
                            "required": ["rule_id", "file_path", "unit_name", "suggested_fix"],
                            "properties": {
                                "rule_id": {"type": "string", "description": "e.g. SRP-1"},
                                "file_path": {"type": "string"},
                                "unit_name": {"type": "string"},
                                "suggested_fix": {"type": "string", "description": "1-3 sentence structural suggestion, no code"},
                            },
                        },
                    },
                },
            },
        },
    },
]


class ToolDispatching(Protocol):
    def dispatch(self, tool_call: dict) -> str: ...


class GatewayToolDispatcher:
    """Routes tool calls to CodebaseSearching, FixInvoking, or FindingsSubmitting."""

    def __init__(
        self,
        codebase_search: CodebaseSearching,
        fix_invoker: FixInvoking,
        parser: ToolCallArgsParsing,
        findings_submitter: Optional[FindingsSubmitting] = None,
    ) -> None:
        self._parser = parser
        self._dispatch_map: dict = {
            "mcp__pipeline__search_codebase": lambda a: codebase_search.search(a.get("query", "")),
            "mcp__pipeline__grep_codebase": lambda a: codebase_search.grep(a.get("name", "")),
            "mcp__pipeline__glob_codebase": lambda a: codebase_search.glob(a.get("pattern", "*")),
            "mcp__pipeline__read_file": lambda a: codebase_search.read(a.get("file_path", "")),
            "mcp__docs__load_fix_for_violation": lambda a: fix_invoker.load_fix(
                a.get("metric_ids") or ([a["metric_id"]] if a.get("metric_id") else [])
            ),
            "mcp__pipeline__submit_fix": lambda a: fix_invoker.submit_fix(
                a.get("output_dir", ""), a.get("fixes", [])
            ),
        }
        if findings_submitter is not None:
            self._dispatch_map["mcp__pipeline__submit_batch_findings"] = lambda a: findings_submitter.submit(
                a.get("output_dir", ""), a.get("submissions", {})
            )

    def dispatch(self, tool_call: dict) -> str:
        try:
            name = tool_call["function"]["name"]
        except (KeyError, TypeError):
            return "error: malformed tool call"

        handler = self._dispatch_map.get(name)
        if handler is None:
            return f"error: unknown tool '{name}'"

        args = self._parser.parse(tool_call)
        return handler(args)
