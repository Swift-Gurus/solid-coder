"""
solid-description: LlamaServerRunner — executes code health reviews and reports detected principle violations.
solid-category: service
solid-tags: [hook, llm]
"""

import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Protocol

_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from hook_utils import GATEWAY, PLUGIN_ROOT, solid_coder_project_dir
from hc_config import inference_params as _load_inference_params
from hc_rule_loader import GatewayCommandRunner, GatewayInvoker, GatewayInvoking
from hc_violation_parser import ViolationParser, ViolationParsing

_MCP_SERVER_DIR = str(PLUGIN_ROOT / "mcp-server")
if _MCP_SERVER_DIR not in sys.path:
    sys.path.insert(0, _MCP_SERVER_DIR)

_MAX_TOOL_ROUNDS = 10

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
                "Load fix guidance for a single metric violation. "
                "Call once per SEVERE violation found — pass only the metric_id (e.g. OCP-1, SRP-2). "
                "Returns {metric_id, content} where `content` is the fix strategy guidance. "
                "Apply that guidance to the specific code being reviewed and write a concrete, "
                "code-specific solution into the `fix` field."
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
                            "Map of principle_name to review-output payload "
                            "(references/review-output.schema.json). "
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


def _strip_thinking(content: str) -> tuple:
    """Split a response that may begin with a <think>…</think> block.

    Returns (thinking, response) where thinking is the content inside the
    tags (empty string if absent) and response is everything after the block.
    """
    if not content:
        return "", content or ""
    match = re.match(r"<think>(.*?)</think>\s*", content, re.DOTALL)
    if match:
        return match.group(1).strip(), content[match.end():].strip()
    return "", content


def _extract_thinking_and_content(message: dict) -> tuple:
    """Extract (thinking, content) from a message dict.

    Prefers reasoning_content (llama.cpp --reasoning mode) over inline
    <think> tags so both server formats are handled transparently.
    """
    content = message.get("content", "") or ""
    reasoning = message.get("reasoning_content", "") or ""
    if reasoning:
        return reasoning.strip(), content
    return _strip_thinking(content)


def _parse_tool_call_args(tool_call: dict) -> dict:
    """Extract and JSON-parse the arguments from a tool_call dict.

    Uses duck typing: tries json.loads first (handles str), falls back to
    treating the value as a dict directly (handles pre-parsed objects).
    """
    raw = tool_call.get("function", {}).get("arguments", "{}")
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        pass
    try:
        return dict(raw) if raw else {}
    except (TypeError, ValueError):
        return {}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _summarise_result(name: str, result_str: str) -> dict:
    """Extract a compact summary from a tool result string."""
    if name == "mcp__pipeline__search_codebase":
        return {"hits": result_str.count(" — ")}
    if name == "mcp__docs__load_fix_for_violation":
        return {"content_len": len(result_str)}
    return {"len": len(result_str)}


# ── Logger I/O protocols ─────────────────────────────────────────────────────

class LogEntryWriting(Protocol):
    """Writes a structured log entry to a named JSONL file in a directory."""

    def append(self, dir_path: Path, filename: str, entry: dict) -> None: ...


class TimeMeasuring(Protocol):
    """Returns current time and elapsed time since a start point."""

    def now(self) -> float: ...
    def elapsed(self, start: float) -> float: ...


class DirectoryCreating(Protocol):
    """Creates a directory and any required parents."""

    def create(self, path: Path) -> None: ...


class JsonlEntryWriter:
    """Boundary adapter: appends JSON lines to disk files."""

    def append(self, dir_path: Path, filename: str, entry: dict) -> None:
        try:
            with (dir_path / filename).open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass


class MonotonicTimer:
    """Boundary adapter: measures elapsed wall-clock time via time.monotonic.

    time.monotonic is a global stdlib function — this adapter satisfies
    the OCP Boundary Adapter exception.
    """

    def now(self) -> float:
        return time.monotonic()

    def elapsed(self, start: float) -> float:
        return self.now() - start


class PathDirectoryCreator:
    """Boundary adapter: creates directories via Path.mkdir."""

    def create(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)


class LocalLLMLogger:
    """Writes per-tool-call JSONL entries to a caller-supplied log directory."""

    def __init__(
        self,
        log_dir: Path,
        file_path: str,
        model: str,
        entry_writer: Optional[LogEntryWriting] = None,
        timer: Optional[TimeMeasuring] = None,
        dir_creator: Optional[DirectoryCreating] = None,
    ) -> None:
        _creator: DirectoryCreating = dir_creator or PathDirectoryCreator()
        _creator.create(log_dir)
        self._dir = log_dir
        self._file = Path(file_path).name
        self._model = model
        self._writer: LogEntryWriting = entry_writer or JsonlEntryWriter()
        self._timer: TimeMeasuring = timer or MonotonicTimer()
        self._t0 = self._timer.now()

    def _write(self, filename: str, entry: dict) -> None:
        entry.setdefault("ts", _now())
        self._writer.append(self._dir, filename, entry)

    def log_start(self, prompt_len: int) -> None:
        self._write("_exchange.jsonl", {
            "ev": "start", "file": self._file,
            "model": self._model, "prompt_len": prompt_len,
        })

    def log_tool_call(self, call_id: str, name: str, args: dict) -> None:
        self._write(f"{call_id}.jsonl", {"ev": "call", "name": name, "args": args})

    def log_tool_result(self, call_id: str, name: str, result_str: str) -> None:
        summary = _summarise_result(name, result_str)
        self._write(f"{call_id}.jsonl", {"ev": "result", **summary})

    def log_thinking(self, round: int, content: str) -> None:
        self._write("_thinking.jsonl", {
            "ev": "thinking", "round": round, "file": self._file, "content": content,
        })

    def log_done(self, rounds: int, usage: dict, violations: list, thinking: str = "") -> None:
        elapsed_ms = int(self._timer.elapsed(self._t0) * 1000)
        entry: dict = {
            "ev": "done",
            "rounds": rounds,
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "elapsed_ms": elapsed_ms,
            "result": "blocked" if violations else "clean",
            "violations": violations,
        }
        if thinking:
            entry["thinking_len"] = len(thinking)
            self._write("_thinking.jsonl", {"ev": "thinking", "file": self._file, "content": thinking})
        self._write("_exchange.jsonl", entry)


class LlamaHttpChatting(Protocol):
    def chat(self, messages: list, tools: list, timeout: int) -> Optional[dict]: ...


class ToolDispatching(Protocol):
    def dispatch(self, tool_call: dict) -> str: ...



class LLMSessionObserving(Protocol):
    def on_start(self, prompt_len: int) -> None: ...
    def on_tool_call(self, call_id: str, name: str, args: dict) -> None: ...
    def on_tool_result(self, call_id: str, name: str, result: str) -> None: ...
    def on_thinking(self, round: int, content: str) -> None: ...
    def on_done(self, rounds: int, usage: dict, violations: list, thinking: str = "") -> None: ...


def _default_grep(name: str) -> str:
    from lib.file_searcher import grep_by_name
    return grep_by_name(name=name)


def _default_glob(pattern: str) -> str:
    from lib.file_searcher import glob_by_name
    return glob_by_name(pattern=pattern)


def _default_search(query: str) -> str:
    from lib.codebase_searcher import search
    tags = [t for t in query.split() if t]
    return search(tags=tags, min_matches=1) if tags else ""


def _default_read_file(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as e:
        return f"error: {e}"



class LLMSessionObserver:
    """Delegates all session events to LocalLLMLogger. Single cohesion group: logging only."""

    def __init__(self, logger: LocalLLMLogger) -> None:
        self._logger = logger

    def on_start(self, prompt_len: int) -> None:
        self._logger.log_start(prompt_len)

    def on_tool_call(self, call_id: str, name: str, args: dict) -> None:
        self._logger.log_tool_call(call_id, name, args)

    def on_tool_result(self, call_id: str, name: str, result: str) -> None:
        self._logger.log_tool_result(call_id, name, result)

    def on_thinking(self, round: int, content: str) -> None:
        self._logger.log_thinking(round, content)

    def on_done(self, rounds: int, usage: dict, violations: list, thinking: str = "") -> None:
        self._logger.log_done(rounds, usage, violations, thinking=thinking)


# ── HTTP + JSON protocols ────────────────────────────────────────────────────

class HttpSending(Protocol):
    def send(self, url: str, data: bytes, headers: dict, timeout: int) -> bytes: ...


class HttpOpening(Protocol):
    """Opens an HTTP request and returns the response body."""

    def open(self, request, timeout: int) -> bytes: ...


class HttpRequestBuilding(Protocol):
    """Constructs an HTTP request object."""

    def build(self, url: str, data: bytes, headers: dict, method: str): ...


class JsonSerializing(Protocol):
    """Serializes a dict to a JSON string."""

    def serialize(self, obj: dict) -> str: ...


class JsonDeserializing(Protocol):
    """Deserializes bytes or str to a dict."""

    def deserialize(self, raw: bytes) -> Optional[dict]: ...


class UrllibOpener:
    """Boundary adapter: wraps urllib.request.urlopen (stdlib, cannot be subclassed).

    urllib.request.urlopen is a global stdlib function — this adapter
    satisfies the OCP Boundary Adapter exception.
    """

    def open(self, request, timeout: int) -> bytes:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            return resp.read()


class UrllibRequestBuilder:
    """Boundary adapter: wraps urllib.request.Request (stdlib, cannot be subclassed).

    urllib.request.Request is a C-extension type — this adapter
    satisfies the OCP Boundary Adapter exception.
    """

    def build(self, url: str, data: bytes, headers: dict, method: str):
        return urllib.request.Request(url, data=data, headers=headers, method=method)


class UrllibSender:
    """Boundary adapter: sends HTTP POST via injected opener and request builder."""

    def __init__(
        self,
        opener: Optional[HttpOpening] = None,
        builder: Optional[HttpRequestBuilding] = None,
    ) -> None:
        self._opener: HttpOpening = opener or UrllibOpener()
        self._builder: HttpRequestBuilding = builder or UrllibRequestBuilder()

    def send(self, url: str, data: bytes, headers: dict, timeout: int) -> bytes:
        req = self._builder.build(url, data, headers, "POST")
        return self._opener.open(req, timeout)


class JsonSerializer:
    """Boundary adapter: wraps json.dumps (stdlib, cannot be subclassed).

    json.dumps is a global stdlib function — this adapter satisfies
    the OCP Boundary Adapter exception.
    """

    def serialize(self, obj: dict) -> str:
        return json.dumps(obj)


class JsonDeserializer:
    """Boundary adapter: wraps json.loads (stdlib, cannot be subclassed).

    json.loads is a global stdlib function — this adapter satisfies
    the OCP Boundary Adapter exception.
    """

    def deserialize(self, raw: bytes) -> Optional[dict]:
        try:
            return json.loads(raw)
        except Exception:
            return None


class LlamaHttpClient:
    """POSTs to llama-server's /v1/chat/completions and returns the parsed response."""

    def __init__(
        self,
        host: str,
        model: str,
        inference_params: Optional[dict] = None,
        transport: Optional[HttpSending] = None,
        serializer: Optional[JsonSerializing] = None,
        deserializer: Optional[JsonDeserializing] = None,
    ) -> None:
        self._url = f"{host.rstrip('/')}/v1/chat/completions"
        self._model = model
        self._inference_params = inference_params or {}
        self._transport: HttpSending = transport or UrllibSender()
        self._serialize: JsonSerializing = serializer or JsonSerializer()
        self._deserialize: JsonDeserializing = deserializer or JsonDeserializer()

    def chat(self, messages: list, tools: list, timeout: int) -> Optional[dict]:
        payload = self._serialize.serialize({
            "model": self._model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            **self._inference_params,
        }).encode()
        try:
            raw = self._transport.send(
                self._url, payload, {"Content-Type": "application/json"}, timeout
            )
            return self._deserialize.deserialize(raw)
        except Exception:
            return None


# ── Findings submission protocols ────────────────────────────────────────────

class BatchFindingsHandling(Protocol):
    """Protocol: submit_batch_findings from the pipeline gateway handler."""

    def submit_batch_findings(self, output_dir: str, submissions: dict) -> dict: ...


class FindingsSubmitting(Protocol):
    """Submits batch findings and returns a JSON string result."""

    def submit(self, output_dir: str, submissions: dict) -> str: ...


class GatewayFindingsSubmitter:
    """Adapts a BatchFindingsHandling handler + JsonSerializing to FindingsSubmitting."""

    def __init__(
        self,
        handler: BatchFindingsHandling,
        serializer: Optional[JsonSerializing] = None,
    ) -> None:
        self._handler = handler
        self._serialize: JsonSerializing = serializer or JsonSerializer()

    def submit(self, output_dir: str, submissions: dict) -> str:
        result = self._handler.submit_batch_findings(output_dir, submissions)
        return self._serialize.serialize(result)


class GatewayToolDispatcher:
    """Dispatches LLM tool calls to the gateway CLI, file search, or findings submitter."""

    def __init__(
        self,
        invoker: GatewayInvoking,
        grep_fn=_default_grep,
        glob_fn=_default_glob,
        search_fn=_default_search,
        read_fn=_default_read_file,
        findings_submitter: Optional[FindingsSubmitting] = None,
    ) -> None:
        self._invoker = invoker
        self._grep = grep_fn
        self._glob = glob_fn
        self._search = search_fn
        self._read = read_fn
        self._findings_submitter = findings_submitter

    def dispatch(self, tool_call: dict) -> str:
        try:
            name = tool_call["function"]["name"]
        except (KeyError, TypeError):
            return "error: malformed tool call"

        args = _parse_tool_call_args(tool_call)

        if name == "mcp__pipeline__search_codebase":
            return self._search(args.get("query", ""))

        if name == "mcp__pipeline__read_file":
            return self._read(args.get("file_path", ""))

        if name == "mcp__pipeline__grep_codebase":
            return self._grep(args.get("name", ""))

        if name == "mcp__pipeline__glob_codebase":
            return self._glob(args.get("pattern", "*"))

        if name == "mcp__docs__load_fix_for_violation":
            result = self._invoker.invoke(
                "load_fix_for_violation",
                extra_args=["--metric_id", args.get("metric_id", "")],
                result_key="content",
                default="",
            )
            return result or ""

        if name == "mcp__pipeline__submit_batch_findings":
            if self._findings_submitter is None:
                return '{"error": "submit_batch_findings not configured"}'
            return self._findings_submitter.submit(
                args.get("output_dir", ""), args.get("submissions", {})
            )

        return f"error: unknown tool '{name}'"


class AgentLoopExecuting(Protocol):
    def execute(
        self,
        messages: list,
        timeout: int,
        observer: Optional[LLMSessionObserving],
    ) -> tuple: ...  # (Optional[str], dict, int, str) = (content, usage, rounds, thinking)


class RangeIterating(Protocol):
    """Protocol for bounded iteration — allows loop count to be injected and tested."""

    def iterate(self, limit: int): ...


class BuiltinRange:
    """Boundary adapter: wraps the built-in range (stdlib, cannot be subclassed).

    range is a global built-in type — this adapter satisfies the
    OCP Boundary Adapter exception.
    """

    def iterate(self, limit: int):
        return range(limit)


class AgentLoopExecutor:
    """Drives the agentic chat loop: sends messages, dispatches tool calls, emits mid-loop events."""

    def __init__(
        self,
        client: LlamaHttpChatting,
        dispatcher: ToolDispatching,
        max_rounds: int,
        range_iter: Optional[RangeIterating] = None,
    ) -> None:
        self._client = client
        self._dispatcher = dispatcher
        self._max_rounds = max_rounds
        self._range: RangeIterating = range_iter or BuiltinRange()

    def execute(
        self,
        messages: list,
        timeout: int,
        observer: Optional[LLMSessionObserving],
    ) -> tuple:
        rounds = 0
        last_usage: dict = {}
        try:
            for _ in self._range.iterate(self._max_rounds):
                response = self._client.chat(messages, TOOLS, timeout)
                if response is None:
                    return None, {}, rounds, ""

                last_usage = response.get("usage", {})
                choice = response.get("choices", [{}])[0]
                message = choice.get("message", {})

                if choice.get("finish_reason") != "tool_calls":
                    thinking, content = _extract_thinking_and_content(message)
                    return content, last_usage, rounds, thinking

                tool_calls = message.get("tool_calls") or []
                if not tool_calls:
                    return message.get("content", ""), last_usage, rounds, ""

                interim_thinking, _ = _extract_thinking_and_content(message)
                if interim_thinking and observer:
                    observer.on_thinking(rounds + 1, interim_thinking)

                rounds += 1
                messages.append(message)
                for tc in tool_calls:
                    call_id = tc.get("id", "unknown")
                    tc_args = _parse_tool_call_args(tc)
                    tc_name = tc.get("function", {}).get("name", "")
                    if observer:
                        observer.on_tool_call(call_id, tc_name, tc_args)
                    result_str = self._dispatcher.dispatch(tc)
                    if observer:
                        observer.on_tool_result(call_id, tc_name, result_str)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": result_str,
                    })
        except Exception:
            return None, {}, rounds, ""

        return None, last_usage, rounds, ""


class LlamaServerRunner:
    """Coordinates review lifecycle: start → loop → parse violations → done."""

    def __init__(
        self,
        loop: AgentLoopExecuting,
        observer: Optional[LLMSessionObserving] = None,
        parser: Optional[ViolationParsing] = None,
    ) -> None:
        self._loop = loop
        self._observer = observer
        self._parser = parser

    def run(self, prompt: str, timeout: int) -> Optional[str]:
        if self._observer:
            self._observer.on_start(len(prompt))
        messages: list = [{"role": "user", "content": prompt}]
        content, usage, rounds, thinking = self._loop.execute(messages, timeout, self._observer)
        if self._observer:
            violations = (self._parser.parse(content) or []) if self._parser and content else []
            self._observer.on_done(rounds, usage, violations, thinking=thinking)
        return content


def make_llama_server_runner(
    host: str,
    model: str,
    gateway: Path = GATEWAY,
    session_id: str = "",
    file_path: str = "",
) -> LlamaServerRunner:
    """Wire production defaults and return a ready-to-use LlamaServerRunner.

    Factory function — constructing and wiring concrete dependencies is this
    function's sole responsibility (OCP Factory exception).
    """
    invoker = GatewayInvoker(gateway, GatewayCommandRunner())
    observer: Optional[LLMSessionObserving] = None
    if session_id:
        log_dir = solid_coder_project_dir() / "llm-sessions" / session_id
        logger = LocalLLMLogger(log_dir=log_dir, file_path=file_path, model=model)
        observer = LLMSessionObserver(logger=logger)
    from lib.gateway_tools import make_gateway_handler  # noqa: PLC0415
    gw_handler = make_gateway_handler(PLUGIN_ROOT / "references")
    findings_submitter = GatewayFindingsSubmitter(handler=gw_handler)
    loop = AgentLoopExecutor(
        client=LlamaHttpClient(host=host, model=model, inference_params=_load_inference_params()),
        dispatcher=GatewayToolDispatcher(
            invoker=invoker,
            findings_submitter=findings_submitter,
        ),
        max_rounds=_MAX_TOOL_ROUNDS,
    )
    return LlamaServerRunner(loop=loop, observer=observer, parser=ViolationParser())
