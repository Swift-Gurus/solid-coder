"""Tests for chunk_tracker.py and enforce_chunk_reads.py."""

import glob
import json
import sys
import tempfile
import time
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

HOOKS_DIR = str(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks")
if HOOKS_DIR not in sys.path:
    sys.path.insert(0, HOOKS_DIR)

import chunk_tracker as tracker
import enforce_chunk_reads as enforcer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tmp() -> str:
    return tempfile.gettempdir()


def _make_chunk(prefix="rules", ts=None, index=1, total=3) -> str:
    ts = ts or int(time.time())
    name = f"solid-coder-{prefix}-{ts}-{index}of{total}.md"
    path = Path(_tmp()) / name
    path.write_text(f"chunk {index} content", encoding="utf-8")
    return str(path)


def _clean_all_chunks() -> None:
    for f in glob.glob(str(Path(_tmp()) / "solid-coder-*.md")):
        Path(f).unlink(missing_ok=True)


def _run_tracker(tool_name: str, session_id: str, **kwargs) -> int:
    import io
    from contextlib import redirect_stdout
    event = {"tool_name": tool_name, "session_id": session_id, **kwargs}
    buf = io.StringIO()
    with patch("sys.stdin", io.StringIO(json.dumps(event))):
        with redirect_stdout(buf):
            try:
                tracker.main()
            except SystemExit as e:
                return e.code or 0
    return 0


def _run_enforcer(tool_name: str, session_id: str) -> tuple:
    import io
    from contextlib import redirect_stdout
    event = {"tool_name": tool_name, "session_id": session_id}
    buf = io.StringIO()
    with patch("sys.stdin", io.StringIO(json.dumps(event))):
        with redirect_stdout(buf):
            try:
                enforcer.main()
            except SystemExit:
                pass
    return buf.getvalue()


def _is_denied(out: str) -> bool:
    if not out:
        return False
    try:
        return json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny"
    except (json.JSONDecodeError, KeyError):
        return False


def _register(session_id: str, *chunk_paths: str) -> None:
    """Simulate the MCP PostToolUse registration step."""
    response_text = "\n".join(f"- {p}" for p in chunk_paths)
    _run_tracker("mcp__plugin_solid-coder_docs__load_rules",
                 session_id, tool_response=response_text)


# ---------------------------------------------------------------------------
# chunk_tracker — MCP registration
# ---------------------------------------------------------------------------

class TestChunkTrackerRegistration(unittest.TestCase):
    def setUp(self):
        self._session = f"test-{uuid.uuid4().hex}"
        self._sf = tracker._state_file(self._session)
        self._sf.unlink(missing_ok=True)
        _clean_all_chunks()

    def tearDown(self):
        self._sf.unlink(missing_ok=True)
        _clean_all_chunks()

    def test_mcp_response_with_chunk_paths_registers_them(self):
        chunk = _make_chunk()
        _register(self._session, chunk)
        state = tracker._load(self._sf)
        self.assertIn(chunk, state["registered"])
        self.assertEqual(state["read"], [])

    def test_mcp_response_without_chunks_ignored(self):
        _run_tracker("mcp__plugin_solid-coder_docs__load_rules",
                     self._session, tool_response="No chunk content here.")
        state = tracker._load(self._sf)
        self.assertEqual(state.get("registered", []), [])

    def test_duplicate_registration_deduplicated(self):
        chunk = _make_chunk()
        _register(self._session, chunk)
        _register(self._session, chunk)
        state = tracker._load(self._sf)
        self.assertEqual(state["registered"].count(chunk), 1)

    def test_non_mcp_tool_does_not_register(self):
        chunk = _make_chunk()
        _run_tracker("Bash", self._session,
                     tool_response=f"- {chunk}")
        state = tracker._load(self._sf)
        self.assertEqual(state.get("registered", []), [])


# ---------------------------------------------------------------------------
# chunk_tracker — Read tracking
# ---------------------------------------------------------------------------

class TestChunkTrackerRead(unittest.TestCase):
    def setUp(self):
        self._session = f"test-{uuid.uuid4().hex}"
        self._sf = tracker._state_file(self._session)
        self._sf.unlink(missing_ok=True)
        _clean_all_chunks()

    def tearDown(self):
        self._sf.unlink(missing_ok=True)
        _clean_all_chunks()

    def test_read_on_chunk_file_recorded(self):
        chunk = _make_chunk()
        _run_tracker("Read", self._session,
                     tool_input={"file_path": chunk})
        state = tracker._load(self._sf)
        self.assertIn(chunk, state["read"])

    def test_read_on_non_chunk_file_ignored(self):
        _run_tracker("Read", self._session,
                     tool_input={"file_path": "/some/regular/file.md"})
        state = tracker._load(self._sf)
        self.assertEqual(state.get("read", []), [])

    def test_duplicate_reads_not_duplicated(self):
        chunk = _make_chunk()
        _run_tracker("Read", self._session, tool_input={"file_path": chunk})
        _run_tracker("Read", self._session, tool_input={"file_path": chunk})
        state = tracker._load(self._sf)
        self.assertEqual(state["read"].count(chunk), 1)

    def test_prune_removes_missing_files(self):
        state = {"registered": ["/tmp/gone.md"], "read": ["/tmp/also-gone.md"]}
        pruned = tracker._prune(state)
        self.assertEqual(pruned["registered"], [])
        self.assertEqual(pruned["read"], [])


# ---------------------------------------------------------------------------
# enforce_chunk_reads — session-isolated enforcement
# ---------------------------------------------------------------------------

class TestEnforceChunkReads(unittest.TestCase):
    def setUp(self):
        self._session = f"test-{uuid.uuid4().hex}"
        self._sf = tracker._state_file(self._session)
        self._sf.unlink(missing_ok=True)
        _clean_all_chunks()

    def tearDown(self):
        self._sf.unlink(missing_ok=True)
        _clean_all_chunks()

    def _make_and_register(self, index=1, total=2) -> str:
        path = _make_chunk(index=index, total=total)
        _register(self._session, path)
        return path

    def test_no_chunks_no_block(self):
        out = _run_enforcer("Bash", self._session)
        self.assertFalse(_is_denied(out))

    def test_read_always_allowed(self):
        self._make_and_register(1, 1)
        out = _run_enforcer("Read", self._session)
        self.assertFalse(_is_denied(out))

    def test_bash_blocked_when_registered_chunk_unread(self):
        self._make_and_register(1, 1)
        out = _run_enforcer("Bash", self._session)
        self.assertTrue(_is_denied(out))

    def test_mcp_blocked_when_chunk_unread(self):
        self._make_and_register(1, 1)
        out = _run_enforcer("mcp__plugin_solid-coder_docs__load_rules", self._session)
        self.assertTrue(_is_denied(out))

    def test_write_blocked_when_chunk_unread(self):
        self._make_and_register(1, 1)
        out = _run_enforcer("Write", self._session)
        self.assertTrue(_is_denied(out))

    def test_all_chunks_read_unblocks(self):
        chunk = self._make_and_register(1, 1)
        _run_tracker("Read", self._session, tool_input={"file_path": chunk})
        out = _run_enforcer("Bash", self._session)
        self.assertFalse(_is_denied(out))

    def test_partial_read_still_blocks(self):
        self._make_and_register(1, 2)
        chunk2 = self._make_and_register(2, 2)
        _run_tracker("Read", self._session, tool_input={"file_path": chunk2})
        out = _run_enforcer("Bash", self._session)
        self.assertTrue(_is_denied(out))

    def test_session_isolation_other_session_chunks_do_not_block(self):
        """Chunks registered by session B must not block session A."""
        other_session = f"other-{uuid.uuid4().hex}"
        other_sf = tracker._state_file(other_session)
        try:
            chunk = _make_chunk()
            _register(other_session, chunk)           # B registers a chunk
            out = _run_enforcer("Bash", self._session)  # A should be unblocked
            self.assertFalse(_is_denied(out))
        finally:
            other_sf.unlink(missing_ok=True)

    def test_expired_registered_chunk_not_blocking(self):
        old_ts = int(time.time()) - enforcer._TTL_SECONDS - 60
        chunk = _make_chunk(ts=old_ts, index=1, total=1)
        _register(self._session, chunk)
        out = _run_enforcer("Bash", self._session)
        self.assertFalse(_is_denied(out))

    def test_deny_message_mentions_chunk_gate(self):
        self._make_and_register(1, 1)
        out = _run_enforcer("Bash", self._session)
        reason = json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("chunk-read-gate", reason)
        self.assertIn("solid-coder-", reason)


if __name__ == "__main__":
    unittest.main()
