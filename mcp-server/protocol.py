"""Minimal MCP (Model Context Protocol) server over stdio.

Supports both transport formats:
  - Newline-delimited JSON (Claude Code plugin MCP — raw JSON + \n)
  - Content-Length framing (LSP-style, used in direct testing)

No external dependencies — works on Python 3.9+.
"""

import json
import sys
from typing import Any, Callable, Dict, Optional


class MCPServer:
    """Minimal MCP server that handles tool registration and stdio transport."""

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self._tools: Dict[str, dict] = {}
        self._handlers: Dict[str, Callable] = {}
        self._transport: str = "unknown"  # detected on first message

    def tool(self, name: str, description: str, input_schema: dict):
        """Register a tool with its handler function."""
        def decorator(fn: Callable):
            self._tools[name] = {
                "name": name,
                "description": description,
                "inputSchema": input_schema,
            }
            self._handlers[name] = fn
            return fn
        return decorator

    def _read_message(self) -> Optional[dict]:
        """Read one JSON-RPC message from stdin.

        Auto-detects transport on the first message:
        - If first byte is '{' → newline-delimited JSON (Claude Code plugin transport)
        - Otherwise → Content-Length framing (LSP-style)
        """
        # Peek at first byte to detect transport
        if self._transport == "unknown":
            first = sys.stdin.buffer.read(1)
            if not first:
                return None
            if first == b"{":
                self._transport = "jsonlines"
            else:
                self._transport = "content-length"
            # Put the byte back by buffering it
            self._peeked = first
        else:
            self._peeked = b""

        if self._transport == "jsonlines":
            return self._read_jsonline()
        else:
            return self._read_content_length()

    def _read_jsonline(self) -> Optional[dict]:
        """Read a newline-terminated JSON message (Claude Code plugin transport)."""
        line = self._peeked + sys.stdin.buffer.readline()
        self._peeked = b""
        if not line or line.strip() == b"":
            return None
        try:
            return json.loads(line.decode("utf-8").strip())
        except json.JSONDecodeError:
            return None

    def _read_content_length(self) -> Optional[dict]:
        """Read a Content-Length framed JSON-RPC message (LSP-style)."""
        headers = {}
        first = self._peeked
        self._peeked = b""
        while True:
            if first:
                raw = first + sys.stdin.buffer.readline()
                first = b""
            else:
                raw = sys.stdin.buffer.readline()
            if not raw:
                return None
            line = raw.decode("utf-8").strip()
            if not line:
                break
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip().lower()] = value.strip()
        length = int(headers.get("content-length", 0))
        if length == 0:
            return None
        body = sys.stdin.buffer.read(length)
        return json.loads(body.decode("utf-8"))

    def _write_message(self, msg: dict) -> None:
        """Write a JSON-RPC response using the detected transport format."""
        if self._transport == "jsonlines":
            body = json.dumps(msg, separators=(",", ":")).encode("utf-8") + b"\n"
            sys.stdout.buffer.write(body)
        else:
            body = json.dumps(msg).encode("utf-8")
            header = f"Content-Length: {len(body)}\r\n\r\n"
            sys.stdout.buffer.write(header.encode("utf-8"))
            sys.stdout.buffer.write(body)
        sys.stdout.buffer.flush()

    def _respond(self, id: Any, result: Any) -> None:
        self._write_message({"jsonrpc": "2.0", "id": id, "result": result})

    def _error(self, id: Any, code: int, message: str) -> None:
        self._write_message({
            "jsonrpc": "2.0", "id": id,
            "error": {"code": code, "message": message},
        })

    def _handle(self, msg: dict) -> None:
        method = msg.get("method", "")
        id = msg.get("id")
        params = msg.get("params", {})

        # Notifications (no id) — acknowledge silently
        if id is None:
            return

        if method == "initialize":
            self._respond(id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": self.name, "version": self.version},
            })
        elif method == "tools/list":
            self._respond(id, {"tools": list(self._tools.values())})
        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            handler = self._handlers.get(tool_name)
            if not handler:
                self._error(id, -32601, f"Unknown tool: {tool_name}")
                return
            try:
                result = handler(**arguments)
                text = result if isinstance(result, str) else json.dumps(result, indent=2)
                is_error = isinstance(result, str) and result.startswith("**")
                display = (
                    f"Show the following output to the user exactly as-is, "
                    f"without summarizing or paraphrasing, then proceed:\n\n{text}"
                )
                self._respond(id, {
                    "content": [{"type": "text", "text": display}],
                    "isError": is_error,
                })
            except Exception as e:
                self._respond(id, {
                    "content": [{"type": "text", "text": json.dumps({"error": str(e)})}],
                    "isError": True,
                })
        else:
            self._error(id, -32601, f"Unknown method: {method}")

    def run(self) -> None:
        """Run the server, reading from stdin until EOF."""
        self._peeked = b""
        while True:
            msg = self._read_message()
            if msg is None:
                break
            self._handle(msg)
