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

from hook_utils import GATEWAY
from hc_rule_loader import GatewayCommandRunner, GatewayInvoker, GatewayInvoking

_MAX_TOOL_ROUNDS = 10

TOOLS: list = [
    {
        "type": "function",
        "function": {
            "name": "search_codebase",
            "description": (
                "Search the codebase for existing implementations or similar types. "
                "Call once per synonym — generate multiple synonyms and call for each."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Type name, synonym, or keyword"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "load_fix_for_violation",
            "description": "Load actionable fix instructions for a specific SOLID metric violation.",
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


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _summarise_result(name: str, result_str: str) -> dict:
    """Extract a compact summary from a gateway tool result string."""
    try:
        data = json.loads(result_str)
        if name == "search_codebase" and isinstance(data, dict):
            return {"hits": len(data.get("results", []))}
        if name == "load_fix_for_violation":
            return {"content_len": len(result_str)}
    except Exception:
        pass
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

    def log_done(self, rounds: int, usage: dict, violations: list) -> None:
        elapsed_ms = int((time.time() - self._t0) * 1000)
        self._write("_exchange.jsonl", {
            "ev": "done",
            "rounds": rounds,
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "elapsed_ms": elapsed_ms,
            "result": "blocked" if violations else "clean",
            "violations": violations,
        })


class LlamaHttpChatting(Protocol):
    def chat(self, messages: list, tools: list, timeout: int) -> Optional[dict]: ...


class ToolDispatching(Protocol):
    def dispatch(self, tool_call: dict) -> str: ...


class LlamaHttpClient:
    """POSTs to llama-server's /v1/chat/completions and returns the parsed response."""

    def __init__(self, host: str, model: str) -> None:
        self._url = f"{host.rstrip('/')}/v1/chat/completions"
        self._model = model

    def chat(self, messages: list, tools: list, timeout: int) -> Optional[dict]:
        payload = json.dumps({
            "model": self._model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0,
        }).encode()
        req = urllib.request.Request(
            self._url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read())
        except Exception:
            return None


class GatewayToolDispatcher:
    """Dispatches LLM tool calls to the gateway CLI and returns JSON string results."""

    def __init__(self, invoker: GatewayInvoking) -> None:
        self._invoker = invoker

    def dispatch(self, tool_call: dict) -> str:
        try:
            name = tool_call["function"]["name"]
            raw = tool_call["function"]["arguments"]
            args = json.loads(raw) if isinstance(raw, str) else raw
        except (KeyError, json.JSONDecodeError, TypeError):
            return "error: malformed tool call"

        if name == "search_codebase":
            result = self._invoker.invoke(
                "search_codebase", extra_args=["--query", args.get("query", "")]
            )
            return json.dumps(result) if result is not None else "[]"

        if name == "load_fix_for_violation":
            result = self._invoker.invoke(
                "load_fix_for_violation", extra_args=["--metric_id", args.get("metric_id", "")]
            )
            return json.dumps(result) if result is not None else ""

        return f"error: unknown tool '{name}'"


class LlamaServerRunner:
    """Agentic loop: sends prompt, executes tool calls until the model returns final content."""

    def __init__(
        self,
        client: LlamaHttpChatting,
        dispatcher: ToolDispatching,
        max_rounds: int = _MAX_TOOL_ROUNDS,
        logger: Optional[LocalLLMLogger] = None,
    ) -> None:
        self._client = client
        self._dispatcher = dispatcher
        self._max_rounds = max_rounds
        self._logger = logger

    def run(self, prompt: str, timeout: int) -> Optional[str]:
        if self._logger:
            self._logger.log_start(len(prompt))
        messages: list = [{"role": "user", "content": prompt}]
        rounds = 0
        last_usage: dict = {}
        try:
            for _ in range(self._max_rounds):
                response = self._client.chat(messages, TOOLS, timeout)
                if response is None:
                    return None

                last_usage = response.get("usage", {})
                choice = response.get("choices", [{}])[0]
                message = choice.get("message", {})

                if choice.get("finish_reason") != "tool_calls":
                    content = message.get("content", "")
                    if self._logger:
                        violations = self._extract_violations(content)
                        self._logger.log_done(rounds, last_usage, violations)
                    return content

                tool_calls = message.get("tool_calls") or []
                if not tool_calls:
                    return message.get("content", "")

                rounds += 1
                messages.append(message)
                for tc in tool_calls:
                    call_id = tc.get("id", "unknown")
                    name = tc.get("function", {}).get("name", "")
                    raw = tc.get("function", {}).get("arguments", "{}")
                    args = json.loads(raw) if isinstance(raw, str) else raw
                    if self._logger:
                        self._logger.log_tool_call(call_id, name, args)
                    result_str = self._dispatcher.dispatch(tc)
                    if self._logger:
                        self._logger.log_tool_result(call_id, name, result_str)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": result_str,
                    })
        except Exception:
            return None

        return None

    @staticmethod
    def _extract_violations(content: str) -> list:
        try:
            return json.loads(content).get("violations", [])
        except Exception:
            return []


def make_llama_server_runner(
    host: str,
    model: str,
    gateway: Path = GATEWAY,
    session_id: str = "",
    file_path: str = "",
) -> LlamaServerRunner:
    """Wire production defaults and return a ready-to-use LlamaServerRunner."""
    invoker = GatewayInvoker(gateway, GatewayCommandRunner())
    logger = LocalLLMLogger(session_id=session_id, file_path=file_path, model=model) if session_id else None
    return LlamaServerRunner(
        client=LlamaHttpClient(host=host, model=model),
        dispatcher=GatewayToolDispatcher(invoker=invoker),
        logger=logger,
    )
