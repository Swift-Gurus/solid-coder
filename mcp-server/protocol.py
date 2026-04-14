"""Minimal MCP (Model Context Protocol) server over stdio.

Implements JSON-RPC 2.0 with content-length framing.
No external dependencies — works on Python 3.9+.
"""

import json
import sys
from typing import Any, Callable, Dict, List, Optional


class MCPServer:
    """Minimal MCP server that handles tool registration and stdio transport."""

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self._tools: Dict[str, dict] = {}
        self._handlers: Dict[str, Callable] = {}

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
        """Read a content-length framed JSON-RPC message from stdin."""
        headers = {}
        while True:
            line = sys.stdin.buffer.readline()
            if not line:
                return None
            line = line.decode("utf-8").strip()
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
        """Write a content-length framed JSON-RPC message to stdout."""
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

        # Notifications (no id) — just acknowledge silently
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
                self._respond(id, {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
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
        while True:
            msg = self._read_message()
            if msg is None:
                break
            self._handle(msg)
