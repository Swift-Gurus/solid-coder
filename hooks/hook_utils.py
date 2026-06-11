#!/usr/bin/env python3
"""
solid-description: Provides infrastructure for hook scripts to handle protocol interactions, logging, command execution, and structured data parsing.
solid-category: utility
"""

import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import IO, Callable, Optional, Protocol

from pydantic import TypeAdapter, ValidationError

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
    return re.sub(r"```[a-zA-Z]*\n?", "", text).strip()


class TypeChecking(Protocol):
    """Protocol for a value type validator used by parse_json_field.

    validate() returns the accepted value, or None if the value does not
    conform to the expected structural shape.
    """

    def validate(self, value: object) -> Optional[object]: ...


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


class StrValidator:
    """TypeChecking: accepts values that support string concatenation (duck-typed str)."""

    def validate(self, value: object) -> Optional[object]:
        try:
            _ = value + ""  # type: ignore[operator]
            return value
        except TypeError:
            return None


class ListValidator:
    """TypeChecking: accepts values that support mutable sequence append (duck-typed list)."""

    def validate(self, value: object) -> Optional[object]:
        try:
            _ = value.append  # type: ignore[union-attr]
            return value
        except AttributeError:
            return None


class ViolationDictValidator:
    """TypeChecking: accepts objects that have string principle, issue, and fix fields.

    Uses duck typing — no isinstance checks. Validates structural shape of LLM
    violation dicts from external JSON output.
    """

    def validate(self, value: object) -> Optional[object]:
        try:
            _ = value["principle"] + ""  # type: ignore[index,operator]
            _ = value["issue"] + ""      # type: ignore[index,operator]
            _ = value["fix"] + ""        # type: ignore[index,operator]
            return value
        except (KeyError, TypeError):
            return None


def parse_hook_event(raw: str) -> Optional[tuple]:
    """Parse a hook PreToolUse event from raw JSON.

    Returns (tool_name, tool_input, file_path, session_id) on success,
    or None when the input is not valid JSON.
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


class Logging(Protocol):
    def log(self, msg: str) -> None: ...


class OutputWriting(Protocol):
    """Protocol for writing a serialised hook payload to an output stream."""

    def write_payload(self, payload: dict) -> None: ...


class StdoutWriter:
    """Adapter: serialises payload to JSON and writes to an injectable stream.

    The stream_factory is resolved lazily at write time so that redirect_stdout
    in tests is respected without eager capture.
    """

    def __init__(self, stream_factory: Callable[[], IO] = lambda: sys.stdout) -> None:
        self._stream_factory = stream_factory

    def write_payload(self, payload: dict) -> None:
        stream = self._stream_factory()
        stream.write(json.dumps(payload))
        stream.flush()


class HookResponding(Protocol):
    def allow(self) -> None: ...
    def block(self, reason: str, additional_context: str = "") -> None: ...
    def allow_with_update(self, updated_input: dict) -> None: ...


class GateHandling(Logging, HookResponding, Protocol):
    """Narrow gate protocol for components that need to log, allow, or block."""


class GateLogger:
    """Appends timestamped log entries to a file. Never raises on I/O errors."""

    def __init__(self, log_path: Optional[Path] = None) -> None:
        self._log_path = log_path or (solid_coder_project_dir() / "gate.log")

    def log(self, msg: str) -> None:
        try:
            self._log_path.parent.mkdir(parents=True, exist_ok=True)
            with self._log_path.open("a") as f:
                f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {msg}\n")
        except Exception:
            pass


class HookResponder:
    """Sends Claude PreToolUse hook protocol responses and exits."""

    def __init__(self, output: OutputWriting = StdoutWriter(), exit_fn=sys.exit) -> None:
        self._output = output
        self._exit = exit_fn

    def _send(self, payload: dict) -> None:
        self._output.write_payload(payload)
        self._exit(0)

    def allow(self) -> None:
        self._exit(0)

    def block(self, reason: str, additional_context: str = "") -> None:
        hook_output: dict = {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
        if additional_context:
            hook_output["additionalContext"] = additional_context
        self._send({"hookSpecificOutput": hook_output})

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
    HookGateFactory to wire production defaults.
    """

    def __init__(self, logger: Logging, responder: HookResponding) -> None:
        self._logger = logger
        self._responder = responder

    def log(self, msg: str) -> None:
        return self._logger.log(msg)

    def allow(self) -> None:
        return self._responder.allow()

    def block(self, reason: str, additional_context: str = "") -> None:
        return self._responder.block(reason, additional_context)

    def allow_with_update(self, updated_input: dict) -> None:
        return self._responder.allow_with_update(updated_input)


class HookGateFactory:
    """Factory: constructs HookGate with production defaults.

    Constructing, holding, and wiring concrete dependencies is inherently
    this class's job (OCP factory exception).
    """

    def __init__(
        self,
        log_path: Optional[Path] = None,
        output: Optional[OutputWriting] = None,
    ) -> None:
        self._log_path = log_path
        self._output = output

    def build(self) -> HookGate:
        return HookGate(
            logger=GateLogger(self._log_path),
            responder=HookResponder(
                output=self._output if self._output is not None else StdoutWriter(),
            ),
        )


class SubprocessError(Exception):
    """Raised when a gate subprocess fails. Carries the reason for display."""


class SubprocessRunning(Protocol):
    """Protocol for executing a shell command and returning captured output."""

    def run(self, cmd: list, timeout: Optional[int] = None, stdin=None, cwd: Optional[str] = None) -> tuple: ...


class SubprocessJsonRunning(Protocol):
    """Protocol for executing a shell command and returning parsed JSON output."""

    def run(self, cmd: list, timeout: Optional[int] = None, stdin=None, cwd: Optional[str] = None) -> object: ...


class SubprocessAdapter:
    """Boundary adapter: wraps subprocess.run for injection.

    subprocess.run is a global stdlib function (not developer-owned, cannot be
    subclassed) — this adapter satisfies the OCP Boundary Adapter exception.
    """

    def run(self, cmd: list, timeout: Optional[int] = None, stdin=None, cwd: Optional[str] = None) -> tuple:
        kwargs: dict = {}
        if timeout is not None:
            kwargs["timeout"] = timeout
        if stdin is not None:
            kwargs["stdin"] = stdin
        if cwd is not None:
            kwargs["cwd"] = cwd
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            raise SubprocessError(f"`{cmd[0]}` timed out after {timeout}s")


class SubprocessJsonRunner:
    """Runs a subprocess command and parses stdout as JSON.

    Reuses SubprocessRunning for execution; adds JSON parsing and error raising.
    """

    def __init__(self, runner: SubprocessRunning) -> None:
        self._runner = runner

    def run(self, cmd: list, timeout: Optional[int] = None, stdin=None, cwd: Optional[str] = None) -> object:
        runner_kwargs: dict = {"timeout": timeout, "stdin": stdin}
        if cwd is not None:
            runner_kwargs["cwd"] = cwd
        try:
            success, stdout, stderr = self._runner.run(cmd, **runner_kwargs)
        except SubprocessError:
            raise
        except Exception as exc:
            raise SubprocessError(f"`{cmd[0]}` failed: {exc}")
        if not success:
            label = " ".join(cmd[:2])
            raise SubprocessError(
                f"`{label}` exited with error" + (f":\n{stderr}" if stderr else "")
            )
        try:
            return json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise SubprocessError(f"`{cmd[0]}` produced invalid JSON: {exc}")


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


class EventParsing(Protocol):
    """Protocol for parsing the JSON event stream from claude -p --bare output."""

    def parse_events(self, raw: object) -> list: ...
    def parse_event_dict(self, event: object) -> Optional[dict]: ...


class PydanticEventParser:
    """Boundary adapter: uses pydantic TypeAdapter to coerce raw output into typed events."""

    def parse_events(self, raw: object) -> list:
        try:
            return TypeAdapter(list).validate_python(raw)
        except ValidationError:
            return [raw]

    def parse_event_dict(self, event: object) -> Optional[dict]:
        try:
            return TypeAdapter(dict).validate_python(event)
        except ValidationError:
            return None


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
