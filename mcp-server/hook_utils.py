#!/usr/bin/env python3
"""
solid-description: Manages project context and orchestrates external tool execution.
solid-category: utility
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional

from type_checking import TypeChecking  # noqa: F401 — re-exported for consumers
from logging_protocol import Logging  # noqa: F401 — re-exported for consumers
from output_writing import OutputWriting  # noqa: F401 — re-exported for consumers
from hook_responding import HookResponding  # noqa: F401 — re-exported for consumers
from gate_handling import GateHandling  # noqa: F401 — re-exported for consumers
from subprocess_error import SubprocessError  # noqa: F401 — re-exported for consumers
from subprocess_running import SubprocessRunning  # noqa: F401 — re-exported for consumers
from subprocess_json_running import SubprocessJsonRunning  # noqa: F401 — re-exported for consumers
from event_parsing import ClaudeBareEventParsing as EventParsing  # noqa: F401 — re-exported for consumers

JSON_OBJ_RE = re.compile(r"\{.*\}", re.DOTALL)

import os as _os

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
GATEWAY = PLUGIN_ROOT / "mcp-server" / "gateway.py"


def solid_coder_slug(project_root: Path) -> str:
    """Derive a Claude-style project slug from an absolute path.

    Mirrors Claude Code's project directory naming convention:
    /Users/alex/Developer/my-project → -Users-alex-Developer-my-project
    """
    return str(project_root.resolve()).replace("/", "-")


def _resolve_project_root(
    env: dict = _os.environ,
    cwd_factory: Callable[[], Path] = Path.cwd,
) -> Path:
    """Boundary: read CLAUDE_PROJECT_DIR from env, fall back to cwd."""
    raw = env.get("CLAUDE_PROJECT_DIR", "")
    return Path(raw) if raw else cwd_factory()


def solid_coder_project_dir(project_root: Optional[Path] = None) -> Path:
    """Return the ~/.solid-coder/{slug}/ base directory for this project."""
    return Path.home() / ".solid-coder" / solid_coder_slug(project_root or _resolve_project_root())


def ensure_on_path(*dirs: Path) -> None:
    """Add each directory to sys.path if not already present."""
    for d in dirs:
        s = str(d)
        if s not in sys.path:
            sys.path.insert(0, s)


def load_toml(path: Path) -> dict:
    """Parse a TOML file using tomllib (3.11+) or tomli backport. Returns {} on any failure."""
    try:
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]
        with open(path, "rb") as f:
            return tomllib.load(f)
    except Exception:
        return {}


def strip_markdown_fences(text: str) -> str:
    """Remove markdown code-fence markers and return stripped text."""
    return re.sub(r"`" * 3 + r"[a-zA-Z]*\n?", "", text).strip()


def parse_json_field(raw: str, key: str, validator: TypeChecking) -> Optional[object]:
    """Strip fences, locate the first JSON object, return validator.validate(value).

    Returns None when the JSON is absent, malformed, the key is missing,
    or validator.validate(value) returns None.
    """
    text = strip_markdown_fences(raw)
    m = JSON_OBJ_RE.search(text)
    if not m:
        return None
    try:
        obj = json.loads(m.group())
        v = obj.get(key)
        if v is None:
            return None
        return validator.validate(v)
    except (json.JSONDecodeError, ValueError):
        return None


from str_validator import StrValidator  # noqa: E402, F401 — re-exported for consumers
from list_validator import ListValidator  # noqa: E402, F401 — re-exported for consumers
from violation_dict_validator import ViolationDictValidator  # noqa: E402, F401 — re-exported for consumers


def parse_hook_event(raw: str) -> Optional[tuple]:
    """Parse a hook PreToolUse event from raw JSON.

    Returns (tool_name, tool_input, file_path, session_id, cwd) on success,
    or None when the input is not valid JSON. `cwd` is the session's true
    working directory as reported by Claude Code — subprocesses spawned from
    this event should be pinned to it rather than inheriting the hook
    process's own ambient cwd.
    """
    try:
        event = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return None
    tool_input = event.get("tool_input") or {}
    return (
        event.get("tool_name", ""),
        tool_input,
        tool_input.get("file_path", ""),
        event.get("session_id", ""),
        event.get("cwd", ""),
    )


def path_matches_pattern(file_path: str, pattern: str) -> bool:
    """Return True if file_path matches the glob pattern.

    Supports ** wildcard: tests/fixtures/** matches any file anywhere under
    that directory, whether the path is relative or absolute.
    Falls back to fnmatch for patterns without **.
    """
    import fnmatch as _fnmatch

    normalized = file_path.replace("\\", "/")
    pat = pattern.replace("\\", "/")

    if "**" in pat:
        prefix = pat.split("**")[0].rstrip("/")
        needle = "/" + prefix + "/"
        haystack = "/" + normalized.lstrip("/")
        return needle in haystack

    return _fnmatch.fnmatch(normalized, pat) or _fnmatch.fnmatch(
        normalized.rsplit("/", 1)[-1], pat
    )


from stdout_writer import StdoutWriter  # noqa: E402, F401 — re-exported for consumers
from gate_logger import GateLogger  # noqa: E402, F401 — re-exported for consumers
from hook_responder import HookResponder  # noqa: E402, F401 — re-exported for consumers
from hook_gate import HookGate  # noqa: E402, F401 — re-exported for consumers
from hook_gate_factory import HookGateFactory  # noqa: E402, F401 — re-exported for consumers
from subprocess_adapter import SubprocessAdapter, SubprocessJsonRunner  # noqa: E402, F401 — re-exported for consumers

_default_subprocess_runner: SubprocessJsonRunning = SubprocessJsonRunner(SubprocessAdapter())


def run_gateway_cmd(
    cmd: list,
    timeout: int = 10,
    *,
    runner: SubprocessJsonRunning = _default_subprocess_runner,
) -> Optional[dict]:
    """Run a gateway CLI command and return parsed JSON dict.

    Raises SubprocessError on failure — callers that need a safe fallback
    should catch it explicitly.
    """
    return runner.run(cmd, timeout=timeout)  # type: ignore[return-value]


from event_parser import PydanticEventParser  # noqa: E402, F401 — re-exported for consumers

_default_event_parser: EventParsing = PydanticEventParser()


def run_claude_bare(
    prompt: str,
    allowed_tools: str = "",
    mcp_config: str = "",
    timeout: int = 300,
    session_id: str = "",
    model: str = "",
    cwd: str = "",
    *,
    runner: SubprocessJsonRunning = _default_subprocess_runner,
    event_parser: EventParsing = _default_event_parser,
) -> Optional[str]:
    """Run claude -p in bare JSON mode and return the final result string.

    Parses the JSON event stream and returns the result field from the last
    result-type event, or None on any failure. When model is non-empty it is
    forwarded as --model (e.g. "claude-haiku-4-5"); when empty the CLI default
    model is used. When cwd is non-empty the subprocess runs in that directory
    so its session transcript lands in the correct project folder.
    """
    cmd = ["claude", "-p", prompt, "--output-format", "json", "--bare"]
    if model:
        cmd += ["--model", model]
    if session_id:
        cmd += ["--session-id", session_id]
    if mcp_config:
        cmd += ["--mcp-config", mcp_config]
    if allowed_tools:
        cmd += ["--allowedTools", allowed_tools]
    run_kwargs: dict = {"timeout": timeout, "stdin": subprocess.DEVNULL}
    if cwd:
        run_kwargs["cwd"] = cwd
    raw = runner.run(cmd, **run_kwargs)
    events = event_parser.parse_events(raw)
    for event in reversed(events):
        event_dict = event_parser.parse_event_dict(event)
        if event_dict is None:
            continue
        if event_dict.get("type") == "result":
            return event_dict.get("result", "")
    raise SubprocessError("claude -p returned no result event")
