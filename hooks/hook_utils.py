#!/usr/bin/env python3
"""
solid-description: Reusable utilities for hook scripts. Provides gate logging,
hook protocol responses, gateway subprocess helper, Claude bare runner, and
shared regex/text-processing utilities. Shared by code_health_check.py and
pre_write_gate.py.
solid-category: utility
"""

import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import IO, Optional, Protocol

JSON_OBJ_RE = re.compile(r"\{.*\}", re.DOTALL)

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
GATEWAY = PLUGIN_ROOT / "mcp-server" / "gateway.py"


def ensure_on_path(*dirs: Path) -> None:
    """Add each directory to sys.path if not already present."""
    for d in dirs:
        s = str(d)
        if s not in sys.path:
            sys.path.insert(0, s)


def strip_markdown_fences(text: str) -> str:
    """Remove markdown code-fence markers and return stripped text."""
    return re.sub(r"```[a-zA-Z]*\n?", "", text).strip()


class Logging(Protocol):
    def log(self, msg: str) -> None: ...


class HookResponding(Protocol):
    def allow(self) -> None: ...
    def block(self, reason: str) -> None: ...
    def allow_with_update(self, updated_input: dict) -> None: ...


class GateLogger:
    """Appends timestamped log entries to a file. Never raises on I/O errors."""

    def __init__(self, log_path: Optional[Path] = None) -> None:
        self._log_path = log_path or Path.home() / ".claude" / "solid-coder-gate.log"

    def log(self, msg: str) -> None:
        try:
            with self._log_path.open("a") as f:
                f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {msg}\n")
        except Exception:
            pass


class HookResponder:
    """Sends Claude PreToolUse hook protocol responses and exits."""

    def __init__(self, output: Optional[IO] = None) -> None:
        self._output = output

    def _send(self, payload: dict) -> None:
        out = self._output if self._output is not None else sys.stdout
        out.write(json.dumps(payload))
        out.flush()
        sys.exit(0)

    def allow(self) -> None:
        sys.exit(0)

    def block(self, reason: str) -> None:
        self._send({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        })

    def allow_with_update(self, updated_input: dict) -> None:
        self._send({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "updatedInput": updated_input,
            }
        })


class HookGate:
    """Pure Facade composing Logging and HookResponding for hook scripts.

    All dependencies are protocol-typed and injected via __init__. Use
    make_hook_gate() to wire production defaults.
    """

    def __init__(self, logger: Logging, responder: HookResponding) -> None:
        self._logger = logger
        self._responder = responder

    def log(self, msg: str) -> None:
        return self._logger.log(msg)

    def allow(self) -> None:
        return self._responder.allow()

    def block(self, reason: str) -> None:
        return self._responder.block(reason)

    def allow_with_update(self, updated_input: dict) -> None:
        return self._responder.allow_with_update(updated_input)


def make_hook_gate(
    log_path: Optional[Path] = None,
    output: Optional[object] = None,
) -> HookGate:
    """Wire production defaults and return a ready-to-use HookGate."""
    return HookGate(
        logger=GateLogger(log_path),
        responder=HookResponder(output),
    )


def _run_subprocess_to_json(cmd: list, timeout: int, stdin=None) -> Optional[object]:
    """Execute cmd, check returncode, parse stdout as JSON, return dict or None."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, stdin=stdin,
        )
        if result.returncode != 0:
            return None
        return json.loads(result.stdout)
    except Exception:
        return None


def run_gateway_cmd(cmd: list, timeout: int = 10) -> Optional[dict]:
    """Run a gateway CLI command and return parsed JSON dict or None on failure."""
    return _run_subprocess_to_json(cmd, timeout=timeout)


def run_claude_bare(
    prompt: str,
    allowed_tools: str = "",
    mcp_config: str = "",
    timeout: int = 300,
    session_id: str = "",
    no_session: bool = False,
) -> Optional[str]:
    """Run `claude -p` in bare JSON mode and return the final result string.

    Parses the JSON event stream and returns the 'result' field from the last
    result-type event, or None on any failure.
    """
    cmd = ["claude", "-p", prompt, "--output-format", "json", "--bare"]
    if session_id:
        cmd += ["--session-id", session_id]
    if no_session:
        cmd += ["--no-session-persistence"]
    if mcp_config:
        cmd += ["--mcp-config", mcp_config]
    if allowed_tools:
        cmd += ["--allowedTools", allowed_tools]
    events = _run_subprocess_to_json(cmd, timeout=timeout, stdin=subprocess.DEVNULL)
    if events is None:
        return None
    if not isinstance(events, list):
        events = [events]
    for obj in reversed(events):
        if isinstance(obj, dict) and obj.get("type") == "result":
            inner = obj.get("result", "")
            return inner if inner.strip() else None
    return None
