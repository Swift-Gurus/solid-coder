"""
solid-description: LlamaServerRunner — agentic loop for local LLM health checks via llama-server's OpenAI-compatible API.
solid-category: service
solid-tags: [hook, llm]
"""

import json
import sys
import urllib.request
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
    ) -> None:
        self._client = client
        self._dispatcher = dispatcher
        self._max_rounds = max_rounds

    def run(self, prompt: str, timeout: int) -> Optional[str]:
        messages: list = [{"role": "user", "content": prompt}]
        try:
            for _ in range(self._max_rounds):
                response = self._client.chat(messages, TOOLS, timeout)
                if response is None:
                    return None

                choice = response.get("choices", [{}])[0]
                message = choice.get("message", {})

                if choice.get("finish_reason") != "tool_calls":
                    return message.get("content", "")

                tool_calls = message.get("tool_calls") or []
                if not tool_calls:
                    return message.get("content", "")

                messages.append(message)
                for tc in tool_calls:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.get("id", ""),
                        "content": self._dispatcher.dispatch(tc),
                    })
        except Exception:
            return None

        return None


def make_llama_server_runner(
    host: str,
    model: str,
    gateway: Path = GATEWAY,
) -> LlamaServerRunner:
    """Wire production defaults and return a ready-to-use LlamaServerRunner."""
    invoker = GatewayInvoker(gateway, GatewayCommandRunner())
    return LlamaServerRunner(
        client=LlamaHttpClient(host=host, model=model),
        dispatcher=GatewayToolDispatcher(invoker=invoker),
    )
