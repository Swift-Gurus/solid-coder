"""Tests for cleanup_pipeline_output.py"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

HOOKS_DIR = str(Path(__file__).resolve().parents[1])
if HOOKS_DIR not in sys.path:
    sys.path.insert(0, HOOKS_DIR)

from cleanup_pipeline_output import (
    PipelineOutputCleaner,
    _extract_output_root,
    _is_safe_path,
    _parse_output_roots,
)


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------

class DebugOn:
    def is_debug(self): return True

class DebugOff:
    def is_debug(self): return False


def _tool_result_line(output_root):
    return json.dumps({
        "type": "user",
        "message": {"content": [{
            "type": "tool_result",
            "content": json.dumps({"output_root": output_root}),
        }]},
    })


def _write_transcript(lines):
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
    for line in lines:
        f.write(line + "\n")
    f.close()
    return f.name


# ---------------------------------------------------------------------------
# _extract_output_root
# ---------------------------------------------------------------------------

class TestExtractOutputRoot(unittest.TestCase):
    def test_string_content(self):
        self.assertEqual(
            _extract_output_root(json.dumps({"output_root": "/a/b"})),
            "/a/b",
        )

    def test_list_content(self):
        content = [{"type": "text", "text": json.dumps({"output_root": "/x"})}]
        self.assertEqual(_extract_output_root(content), "/x")

    def test_missing_key_returns_empty(self):
        self.assertEqual(_extract_output_root(json.dumps({"other": "val"})), "")

    def test_malformed_json_returns_empty(self):
        self.assertEqual(_extract_output_root("not json"), "")

    def test_empty_string_returns_empty(self):
        self.assertEqual(_extract_output_root(""), "")


# ---------------------------------------------------------------------------
# _parse_output_roots
# ---------------------------------------------------------------------------

class TestParseOutputRoots(unittest.TestCase):
    def test_single_result(self):
        path = _write_transcript([_tool_result_line("/home/user/.solid-coder/review-123")])
        self.assertEqual(_parse_output_roots(path), ["/home/user/.solid-coder/review-123"])

    def test_multiple_results(self):
        path = _write_transcript([
            _tool_result_line("/a/review-1"),
            _tool_result_line("/a/refactor-2"),
        ])
        self.assertEqual(_parse_output_roots(path), ["/a/review-1", "/a/refactor-2"])

    def test_deduplication(self):
        path = _write_transcript([
            _tool_result_line("/a/review-1"),
            _tool_result_line("/a/review-1"),
        ])
        self.assertEqual(_parse_output_roots(path), ["/a/review-1"])

    def test_no_tool_results_returns_empty(self):
        path = _write_transcript([
            json.dumps({"type": "assistant", "message": {"content": []}}),
        ])
        self.assertEqual(_parse_output_roots(path), [])

    def test_malformed_lines_skipped(self):
        path = _write_transcript(["not json", _tool_result_line("/a/b")])
        self.assertEqual(_parse_output_roots(path), ["/a/b"])

    def test_missing_file_returns_empty(self):
        self.assertEqual(_parse_output_roots("/nonexistent/path.jsonl"), [])


# ---------------------------------------------------------------------------
# _is_safe_path
# ---------------------------------------------------------------------------

class TestIsSafePath(unittest.TestCase):
    def test_path_under_solid_coder(self):
        safe = str(Path.home() / ".solid-coder" / "review-123")
        self.assertTrue(_is_safe_path(safe))

    def test_path_outside_solid_coder(self):
        self.assertFalse(_is_safe_path("/tmp/some-dir"))

    def test_home_root_itself_is_not_safe(self):
        self.assertFalse(_is_safe_path(str(Path.home())))

    def test_empty_string_is_not_safe(self):
        self.assertFalse(_is_safe_path(""))


# ---------------------------------------------------------------------------
# PipelineOutputCleaner
# ---------------------------------------------------------------------------

class TestPipelineOutputCleanerShouldHandle(unittest.TestCase):
    def test_returns_true_when_transcript_path_present(self):
        c = PipelineOutputCleaner(debug_reader=DebugOff())
        self.assertTrue(c.should_handle({"transcript_path": "/some/path.jsonl"}))

    def test_returns_false_when_transcript_path_absent(self):
        c = PipelineOutputCleaner(debug_reader=DebugOff())
        self.assertFalse(c.should_handle({}))


class TestPipelineOutputCleanerHandle(unittest.TestCase):
    def _make_safe_dir(self):
        base = Path.home() / ".solid-coder"
        base.mkdir(exist_ok=True)
        d = base / "test-cleanup-review-999"
        d.mkdir(exist_ok=True)
        return str(d)

    def test_deletes_safe_path_when_debug_off(self):
        d = self._make_safe_dir()
        path = _write_transcript([_tool_result_line(d)])
        c = PipelineOutputCleaner(debug_reader=DebugOff())
        c.handle({"transcript_path": path})
        self.assertFalse(Path(d).exists())

    def test_preserves_path_when_debug_on(self):
        d = self._make_safe_dir()
        path = _write_transcript([_tool_result_line(d)])
        c = PipelineOutputCleaner(debug_reader=DebugOn())
        c.handle({"transcript_path": path})
        self.assertTrue(Path(d).exists())
        Path(d).rmdir()

    def test_skips_unsafe_path(self):
        path = _write_transcript([_tool_result_line("/tmp/should-not-delete")])
        c = PipelineOutputCleaner(debug_reader=DebugOff())
        c.handle({"transcript_path": path})  # must not raise

    def test_no_op_when_no_tool_results(self):
        path = _write_transcript([json.dumps({"type": "assistant", "message": {"content": []}})])
        c = PipelineOutputCleaner(debug_reader=DebugOff())
        c.handle({"transcript_path": path})  # must not raise


if __name__ == "__main__":
    unittest.main()
