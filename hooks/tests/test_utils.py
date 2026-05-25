"""Shared test fixtures and helpers for hook tests."""

import io
import json
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

LONG_SWIFT = "import Foundation\n\nfinal class Foo {\n" + "    func bar() {}\n" * 35 + "}\n"
SHORT_SWIFT = "final class Foo {\n    func bar() {}\n}\n"


def call_main(stdin_input, main_fn) -> tuple:
    """Invoke main_fn with faked stdin, capture stdout, return (exit_code, output).

    stdin_input may be a dict (JSON-serialised automatically) or a raw str
    (used as-is, allowing callers to inject invalid JSON for error-path tests).
    """
    raw = stdin_input if isinstance(stdin_input, str) else json.dumps(stdin_input)
    buf = io.StringIO()
    code = 0
    with patch("sys.stdin", io.StringIO(raw)):
        with redirect_stdout(buf):
            try:
                main_fn()
            except SystemExit as e:
                code = e.code or 0
    return code, buf.getvalue()


def call_main_with_invalid_stdin(main_fn) -> tuple:
    """Invoke main_fn with non-JSON stdin; returns (exit_code, output)."""
    return call_main("not json", main_fn)


def make_subprocess_mock(returncode: int, stdout_obj) -> MagicMock:
    """Build a subprocess.run MagicMock with the given returncode and JSON-encoded stdout."""
    m = MagicMock()
    m.returncode = returncode
    m.stdout = json.dumps(stdout_obj)
    return m


def is_denied(out: str) -> bool:
    """Return True if the hook output represents a deny decision."""
    if not out:
        return False
    return json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny"


def parse_hook_output(out: str) -> dict:
    """Extract the hookSpecificOutput dict from a gate hook's JSON stdout."""
    return json.loads(out)["hookSpecificOutput"]


def event(tool: str, path: str, content: str) -> dict:
    """Build a Write or Edit tool event dict."""
    key = "content" if tool == "Write" else "new_string"
    inp = {"file_path": path, key: content}
    if tool == "Edit":
        inp["old_string"] = "old"
    return {"tool_name": tool, "tool_input": inp, "session_id": "test"}
