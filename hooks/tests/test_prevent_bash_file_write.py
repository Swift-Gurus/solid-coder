"""Tests for prevent_bash_file_write.py"""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

HOOKS_DIR = str(Path(__file__).resolve().parents[1])
if HOOKS_DIR not in sys.path:
    sys.path.insert(0, HOOKS_DIR)

import prevent_bash_file_write as hook


def _call(command: str) -> tuple:
    import io
    from contextlib import redirect_stdout
    event = {"tool_name": "Bash", "tool_input": {"command": command}}
    buf = io.StringIO()
    code = 0
    with patch("sys.stdin", io.StringIO(json.dumps(event))):
        with redirect_stdout(buf):
            try:
                hook.main()
            except SystemExit as e:
                code = e.code or 0
    return code, buf.getvalue()


def _is_denied(out: str) -> bool:
    if not out:
        return False
    return json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny"


def _is_allowed(out: str) -> bool:
    return not out


class TestFileWriteDetection(unittest.TestCase):
    # --- should block ---
    def test_blocks_tee(self):
        _, out = _call("echo hello | tee output.txt")
        self.assertTrue(_is_denied(out))

    def test_blocks_cat_redirect(self):
        _, out = _call("cat > /tmp/file.swift << 'EOF'\ncode\nEOF")
        self.assertTrue(_is_denied(out))

    def test_blocks_echo_redirect(self):
        _, out = _call('echo "content" > file.py')
        self.assertTrue(_is_denied(out))

    def test_blocks_append_redirect(self):
        _, out = _call("echo line >> log.txt")
        self.assertTrue(_is_denied(out))

    def test_blocks_heredoc_to_file(self):
        _, out = _call("cat << 'EOF' > /src/Foo.swift\ncode\nEOF")
        self.assertTrue(_is_denied(out))

    def test_blocks_printf_redirect(self):
        _, out = _call('printf "%s\n" hello > file.txt')
        self.assertTrue(_is_denied(out))

    # --- should allow ---
    def test_allows_redirect_to_devnull(self):
        _, out = _call("command > /dev/null")
        self.assertTrue(_is_allowed(out))

    def test_allows_stderr_redirect(self):
        _, out = _call("command 2>&1")
        self.assertTrue(_is_allowed(out))

    def test_allows_stderr_to_devnull(self):
        _, out = _call("command 2>/dev/null")
        self.assertTrue(_is_allowed(out))

    def test_allows_read_redirect(self):
        _, out = _call("wc -l < file.txt")
        self.assertTrue(_is_allowed(out))

    def test_allows_grep(self):
        _, out = _call("grep pattern file.swift")
        self.assertTrue(_is_allowed(out))

    def test_allows_ls(self):
        _, out = _call("ls -la")
        self.assertTrue(_is_allowed(out))

    def test_allows_non_bash_tool(self):
        import io
        from contextlib import redirect_stdout
        event = {"tool_name": "Write", "tool_input": {"file_path": "/tmp/f.swift", "content": "x"}}
        buf = io.StringIO()
        with patch("sys.stdin", io.StringIO(json.dumps(event))):
            with redirect_stdout(buf):
                try:
                    hook.main()
                except SystemExit:
                    pass
        self.assertTrue(_is_allowed(buf.getvalue()))

    def test_deny_message_mentions_write_tool(self):
        _, out = _call("echo hello > file.swift")
        payload = json.loads(out)
        reason = payload["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("Write tool", reason)
        self.assertIn("file-write-gate", reason)


if __name__ == "__main__":
    unittest.main()
