"""
solid-description: LlamaServerRunner — agentic loop for local LLM health checks via llama-server's OpenAI-compatible API.
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

from hook_utils import GATEWAY, PLUGIN_ROOT
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
    """Extract and JSON-parse the arguments from a tool_call dict."""
    raw = tool_call.get("function", {}).get("arguments", "{}")
    try:
        return json.loads(raw) if isinstance(raw, str) else (raw or {})
    except (json.JSONDecodeError, TypeError):
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


class LocalLLMLogger:
    """Writes per-tool-call JSONL entries to ~/.solid-coder/llm-sessions/."""

    ROOT = Path.home() / ".solid-coder" / "llm-sessions"

    def __init__(self, session_id: str, file_path: str, model: str) -> None:
        slug = re.sub(r"[^a-zA-Z0-9-]", "_", Path.cwd().name or "unknown")
        self._dir = self.ROOT / slug / (session_id or "no-session")
        self._dir.mkdir(parents=True, exist_ok=True)
        self._file = Path(file_path).name
        self._model = model
        self._t0 = time.time()

    def _write(self, filename: str, entry: dict) -> None:
        entry.setdefault("ts", _now())
        try:
            with (self._dir / filename).open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

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
        elapsed_ms = int((time.time() - self._t0) * 1000)
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


class FileSearching(Protocol):
    def grep_by_name(self, name: str) -> str: ...
    def glob_by_name(self, pattern: str) -> str: ...
    def search_codebase(self, query: str) -> str: ...
    def read_file(self, path: str) -> str: ...


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


class FileSearcher:
    """Adapter wrapping file-search callables behind the FileSearching protocol."""

    def __init__(
        self,
        grep_fn=_default_grep,
        glob_fn=_default_glob,
        search_fn=_default_search,
        read_fn=_default_read_file,
    ) -> None:
        self._grep = grep_fn
        self._glob = glob_fn
        self._search = search_fn
        self._read = read_fn

    def grep_by_name(self, name: str) -> str:
        return self._grep(name)

    def glob_by_name(self, pattern: str) -> str:
        return self._glob(pattern)

    def search_codebase(self, query: str) -> str:
        return self._search(query)

    def read_file(self, path: str) -> str:
        return self._read(path)


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


class HttpSending(Protocol):
    def send(self, url: str, data: bytes, headers: dict, timeout: int) -> bytes: ...


class UrllibSender:
    """Sends HTTP POST requests using urllib.request."""

    def send(self, url: str, data: bytes, headers: dict, timeout: int) -> bytes:
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()


class LlamaHttpClient:
    """POSTs to llama-server's /v1/chat/completions and returns the parsed response."""

    def __init__(
        self,
        host: str,
        model: str,
        inference_params: Optional[dict] = None,
        transport: Optional[HttpSending] = None,
    ) -> None:
        self._url = f"{host.rstrip('/')}/v1/chat/completions"
        self._model = model
        self._inference_params = inference_params or {}
        self._transport: HttpSending = transport or UrllibSender()

    def chat(self, messages: list, tools: list, timeout: int) -> Optional[dict]:
        payload = json.dumps({
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
            return json.loads(raw)
        except Exception:
            return None


class GatewayToolDispatcher:
    """Dispatches LLM tool calls to the gateway CLI or injected file search."""

    def __init__(self, invoker: GatewayInvoking, file_searcher: FileSearching) -> None:
        self._invoker = invoker
        self._file_searcher = file_searcher

    def dispatch(self, tool_call: dict) -> str:
        try:
            name = tool_call["function"]["name"]
        except (KeyError, TypeError):
            return "error: malformed tool call"

        args = _parse_tool_call_args(tool_call)

        if name == "mcp__pipeline__search_codebase":
            return self._file_searcher.search_codebase(args.get("query", ""))

        if name == "mcp__pipeline__read_file":
            return self._file_searcher.read_file(args.get("file_path", ""))

        if name == "mcp__pipeline__grep_codebase":
            return self._file_searcher.grep_by_name(args.get("name", ""))

        if name == "mcp__pipeline__glob_codebase":
            return self._file_searcher.glob_by_name(args.get("pattern", "*"))

        if name == "mcp__docs__load_fix_for_violation":
            result = self._invoker.invoke(
                "load_fix_for_violation",
                extra_args=["--metric_id", args.get("metric_id", "")],
                result_key="content",
                default="",
            )
            return result or ""

        return f"error: unknown tool '{name}'"


class AgentLoopExecuting(Protocol):
    def execute(
        self,
        messages: list,
        timeout: int,
        observer: Optional[LLMSessionObserving],
    ) -> tuple: ...  # (Optional[str], dict, int, str) = (content, usage, rounds, thinking)


class AgentLoopExecutor:
    """Drives the agentic chat loop: sends messages, dispatches tool calls, emits mid-loop events."""

    def __init__(
        self,
        client: LlamaHttpChatting,
        dispatcher: ToolDispatching,
        max_rounds: int = _MAX_TOOL_ROUNDS,
    ) -> None:
        self._client = client
        self._dispatcher = dispatcher
        self._max_rounds = max_rounds

    def execute(
        self,
        messages: list,
        timeout: int,
        observer: Optional[LLMSessionObserving],
    ) -> tuple:
        rounds = 0
        last_usage: dict = {}
        try:
            for _ in range(self._max_rounds):
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
    """Wire production defaults and return a ready-to-use LlamaServerRunner."""
    invoker = GatewayInvoker(gateway, GatewayCommandRunner())
    observer: Optional[LLMSessionObserving] = None
    if session_id:
        logger = LocalLLMLogger(session_id=session_id, file_path=file_path, model=model)
        observer = LLMSessionObserver(logger=logger)
    loop = AgentLoopExecutor(
        client=LlamaHttpClient(host=host, model=model, inference_params=_load_inference_params()),
        dispatcher=GatewayToolDispatcher(invoker=invoker, file_searcher=FileSearcher()),
    )
    return LlamaServerRunner(loop=loop, observer=observer, parser=ViolationParser())
