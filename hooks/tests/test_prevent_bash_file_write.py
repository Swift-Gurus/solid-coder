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
        _, out = _call("echo hello | tee output.swift")
        self.assertTrue(_is_denied(out))

    def test_blocks_cat_redirect(self):
        _, out = _call("cat > /tmp/file.swift << 'EOF'\ncode\nEOF")
        self.assertTrue(_is_denied(out))

    def test_blocks_echo_redirect(self):
        _, out = _call('echo "content" > file.swift')
        self.assertTrue(_is_denied(out))

    def test_blocks_append_redirect(self):
        _, out = _call("echo line >> log.swift")
        self.assertTrue(_is_denied(out))

    def test_blocks_heredoc_to_file(self):
        _, out = _call("cat << 'EOF' > /src/Foo.swift\ncode\nEOF")
        self.assertTrue(_is_denied(out))

    def test_blocks_printf_redirect(self):
        _, out = _call('printf "%s\n" hello > file.swift')
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

    def test_blocks_python3_multiline_write(self):
        """python3 -c with open(..., 'w') on a different line than python3 must be blocked."""
        cmd = (
            "python3 -c \"\n"
            "files = ['Foo.swift']\n"
            "for f in files:\n"
            "    with open(f, 'w') as fp:\n"
            "        fp.write('content')\n"
            "\""
        )
        _, out = _call(cmd)
        self.assertTrue(_is_denied(out))

    def test_allows_python3_multiline_read_only(self):
        """python3 -c that only reads files must be allowed."""
        cmd = (
            "python3 -c \"\n"
            "files = ['Foo.swift', 'Bar.swift']\n"
            "for f in files:\n"
            "    with open(f, 'rb') as fp:\n"
            "        n = len(fp.read()) - len(fp.read().rstrip(b'\\n'))\n"
            "        print(n, f)\n"
            "\""
        )
        _, out = _call(cmd)
        self.assertTrue(_is_allowed(out))

    def test_blocks_python3_write_binary_mode(self):
        """open(path, 'wb') must be blocked — not just bare 'w'."""
        cmd = "python3 -c \"open('/src/Foo.swift', 'wb').write(b'x')\""
        _, out = _call(cmd)
        self.assertTrue(_is_denied(out))

    def test_blocks_python3_append_binary_mode(self):
        """open(path, 'ab') must be blocked."""
        cmd = "python3 -c \"open('/src/Foo.swift', 'ab').write(b'x')\""
        _, out = _call(cmd)
        self.assertTrue(_is_denied(out))

    def test_blocks_python3_write_plus_mode(self):
        """open(path, 'w+') must be blocked."""
        cmd = "python3 -c \"open('/src/Foo.swift', 'w+').write('x')\""
        _, out = _call(cmd)
        self.assertTrue(_is_denied(out))

    def test_allows_python3_read_binary_mode(self):
        """open(path, 'rb') — read binary — must be allowed."""
        cmd = "python3 -c \"open('/src/Foo.swift', 'rb').read()\""
        _, out = _call(cmd)
        self.assertTrue(_is_allowed(out))


class TestChunkFileReadDetection(unittest.TestCase):
    """Bash must not be used to read MCP chunk files — use the Read tool instead."""

    def test_blocks_cat_on_linux_tmp_chunk(self):
        _, out = _call("cat /tmp/solid-coder-rules-1778776938-1of3.md")
        self.assertTrue(_is_denied(out))

    def test_blocks_cat_n_on_macos_chunk(self):
        _, out = _call(
            "cat -n /var/folders/42/g1w_3hns2js4clrz6h42v0600000gp/T/"
            "solid-coder-spec-context-SPEC-046-1778776938-1of3.md"
        )
        self.assertTrue(_is_denied(out))

    def test_blocks_tail_on_chunk(self):
        _, out = _call("tail -n 50 /tmp/solid-coder-rules-1234-2of3.md")
        self.assertTrue(_is_denied(out))

    def test_blocks_head_on_chunk(self):
        _, out = _call("head -n 100 /tmp/solid-coder-rules-1234-3of3.md")
        self.assertTrue(_is_denied(out))

    def test_blocks_any_bash_referencing_chunk_prefix(self):
        _, out = _call("wc -l /tmp/solid-coder-fixes-9999-1of2.md")
        self.assertTrue(_is_denied(out))

    def test_deny_message_mentions_read_tool(self):
        _, out = _call("cat /tmp/solid-coder-rules-1234-1of1.md")
        reason = json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("Read tool", reason)
        self.assertIn("chunk-read-gate", reason)

    def test_allows_unrelated_tmp_file(self):
        _, out = _call("cat /tmp/some-other-file.md")
        self.assertTrue(_is_allowed(out))

    def test_allows_grep_not_targeting_chunk(self):
        _, out = _call("grep pattern /tmp/output.txt")
        self.assertTrue(_is_allowed(out))


if __name__ == "__main__":
    unittest.main()
