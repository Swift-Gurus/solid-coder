"""
solid-description: Dispatches LLM tool calls to their corresponding handlers.
solid-category: service
solid-tags: [hook, llm]
"""

from typing import Callable, Optional, Protocol

from llama.findings_submitter import FindingsSubmitting
from llama.tool_call_parser import ToolCallArgsParsing


TOOLS: list = [
    {
        "type": "function",
        "function": {
            "name": "mcp__plugin_solid-coder_pipeline__search_codebase",
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
            "name": "mcp__plugin_solid-coder_pipeline__grep_codebase",
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
            "name": "mcp__plugin_solid-coder_pipeline__glob_codebase",
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
            "name": "mcp__plugin_solid-coder_pipeline__read_file",
            "description": (
                "Read the full source code of a file by its absolute path. "
                "Use this after mcp__plugin_solid-coder_pipeline__search_codebase returns matches — for each matched "
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
            "name": "mcp__plugin_solid-coder_docs__load_fix_for_violation",
            "description": (
                "Load fix guidance for a single metric violation. "
                "Call once per SEVERE violation found — pass only the metric_id (e.g. OCP-1, SRP-2). "
                "Returns {metric_id, content} where `content` is the fix strategy guidance."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "metric_id": {"type": "string", "description": "Metric identifier e.g. OCP-1, SRP-2"},
                },
                "required": ["metric_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mcp__plugin_solid-coder_pipeline__submit_batch_findings",
            "description": (
                "Submit findings for all reviewed principles in one unified payload. "
                "Discovers principle keys from metrics, scores each, writes "
                "output_dir/{principle}/review-output.json. "
                "YOU MUST call this tool to complete the workflow — do not write findings as text."
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
                            "E.g. {'SRP': {timestamp, files:[{file_path, units:[{unit_name, unit_kind, "
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
                                        "required": ["file_path", "units"],
                                        "properties": {
                                            "file_path": {"type": "string"},
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
]


class ToolDispatching(Protocol):
    def dispatch(self, tool_call: dict) -> str: ...


class GatewayToolDispatcher:
    """Dispatches LLM tool calls to the gateway CLI, file search, or findings submitter."""

    def __init__(
        self,
        invoker,
        grep_fn: Callable[[str], str],
        glob_fn: Callable[[str], str],
        search_fn: Callable[[str], str],
        read_fn: Callable[[str], str],
        parser: ToolCallArgsParsing,
        findings_submitter: Optional[FindingsSubmitting] = None,
    ) -> None:
        self._invoker = invoker
        self._grep = grep_fn
        self._glob = glob_fn
        self._search = search_fn
        self._read = read_fn
        self._parser = parser
        self._findings_submitter = findings_submitter

    def dispatch(self, tool_call: dict) -> str:
        try:
            name = tool_call["function"]["name"]
        except (KeyError, TypeError):
            return "error: malformed tool call"

        args = self._parser.parse(tool_call)

        if name == "mcp__plugin_solid-coder_pipeline__search_codebase":
            return self._search(args.get("query", ""))

        if name == "mcp__plugin_solid-coder_pipeline__read_file":
            return self._read(args.get("file_path", ""))

        if name == "mcp__plugin_solid-coder_pipeline__grep_codebase":
            return self._grep(args.get("name", ""))

        if name == "mcp__plugin_solid-coder_pipeline__glob_codebase":
            return self._glob(args.get("pattern", "*"))

        if name == "mcp__plugin_solid-coder_docs__load_fix_for_violation":
            result = self._invoker.invoke(
                "load_fix_for_violation",
                extra_args=["--metric_id", args.get("metric_id", "")],
                result_key="content",
                default="",
            )
            return result or ""

        if name == "mcp__plugin_solid-coder_pipeline__submit_batch_findings":
            if self._findings_submitter is None:
                return '{"error": "submit_batch_findings not configured"}'
            return self._findings_submitter.submit(
                args.get("output_dir", ""), args.get("submissions", {})
            )

        return f"error: unknown tool '{name}'"
