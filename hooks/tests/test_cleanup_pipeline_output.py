"""Tests for cleanup_pipeline_output.py"""

import sys
import unittest
from pathlib import Path

HOOKS_DIR = str(Path(__file__).resolve().parents[1])
if HOOKS_DIR not in sys.path:
    sys.path.insert(0, HOOKS_DIR)

from cleanup_pipeline_output import (
    HcConfigDebugReader,
    PathCleanupOrchestrator,
    PipelineOutputCleaner,
    SafeRootValidator,
    SentinelFileReader,
    ShutilDirectoryRemover,
    StopEventFilter,
    _extract_output_root,
)


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------

class DebugOn:
    def is_debug(self): return True

class DebugOff:
    def is_debug(self): return False


class FakeSentinel:
    def __init__(self, roots=None):
        self._roots = list(roots or [])
        self.cleared = False

    def get_pending_roots(self): return list(self._roots)
    def clear(self): self.cleared = True


class FakeValidator:
    def __init__(self, safe=True): self._safe = safe
    def is_safe(self, path): return self._safe


class RecordingRemover:
    def __init__(self): self.removed = []
    def remove(self, path): self.removed.append(path)


class AlwaysFilter:
    def should_handle(self, event): return True

class NeverFilter:
    def should_handle(self, event): return False


class RecordingOrchestrator:
    def __init__(self): self.handled = []
    def handle(self, event): self.handled.append(event)


# ---------------------------------------------------------------------------
# _extract_output_root
# ---------------------------------------------------------------------------

class TestExtractOutputRoot(unittest.TestCase):
    def test_string_content(self):
        import json
        self.assertEqual(
            _extract_output_root(json.dumps({"output_root": "/a/b"})),
            "/a/b",
        )

    def test_list_content(self):
        import json
        content = [{"type": "text", "text": json.dumps({"output_root": "/x"})}]
        self.assertEqual(_extract_output_root(content), "/x")

    def test_missing_key_returns_empty(self):
        import json
        self.assertEqual(_extract_output_root(json.dumps({"other": "val"})), "")

    def test_malformed_json_returns_empty(self):
        self.assertEqual(_extract_output_root("not json"), "")

    def test_empty_string_returns_empty(self):
        self.assertEqual(_extract_output_root(""), "")


# ---------------------------------------------------------------------------
# SentinelFileReader
# ---------------------------------------------------------------------------

class TestSentinelFileReader(unittest.TestCase):
    def _make(self, content=""):
        import tempfile
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
        f.write(content)
        f.close()
        return SentinelFileReader(sentinel=Path(f.name))

    def test_reads_paths(self):
        r = self._make("/a/b\n/c/d\n")
        self.assertEqual(r.get_pending_roots(), ["/a/b", "/c/d"])

    def test_empty_file_returns_empty(self):
        r = self._make("")
        self.assertEqual(r.get_pending_roots(), [])

    def test_missing_file_returns_empty(self):
        r = SentinelFileReader(sentinel=Path("/nonexistent/.pending"))
        self.assertEqual(r.get_pending_roots(), [])

    def test_clear_removes_file(self):
        r = self._make("/a")
        r.clear()
        self.assertFalse(Path(r._sentinel).exists())


# ---------------------------------------------------------------------------
# SafeRootValidator
# ---------------------------------------------------------------------------

class TestSafeRootValidator(unittest.TestCase):
    def setUp(self):
        self.v = SafeRootValidator(safe_root=Path("/safe/root"))

    def test_path_under_root_is_safe(self):
        self.assertTrue(self.v.is_safe("/safe/root/review-123"))

    def test_path_outside_root_is_not_safe(self):
        self.assertFalse(self.v.is_safe("/tmp/other"))

    def test_empty_path_is_not_safe(self):
        self.assertFalse(self.v.is_safe(""))


# ---------------------------------------------------------------------------
# PathCleanupOrchestrator
# ---------------------------------------------------------------------------

class TestPathCleanupOrchestrator(unittest.TestCase):
    def _make(self, roots, safe=True, debug=False):
        remover = RecordingRemover()
        sentinel = FakeSentinel(roots)
        orch = PathCleanupOrchestrator(
            debug_reader=DebugOn() if debug else DebugOff(),
            sentinel_reader=sentinel,
            validator=FakeValidator(safe=safe),
            remover=remover,
        )
        return orch, remover, sentinel

    def test_deletes_safe_roots(self):
        orch, remover, sentinel = self._make(["/safe/a", "/safe/b"])
        orch.handle({})
        self.assertEqual(remover.removed, ["/safe/a", "/safe/b"])
        self.assertTrue(sentinel.cleared)

    def test_skips_unsafe_roots(self):
        orch, remover, sentinel = self._make(["/unsafe/a"], safe=False)
        orch.handle({})
        self.assertEqual(remover.removed, [])
        self.assertTrue(sentinel.cleared)

    def test_debug_mode_skips_all(self):
        orch, remover, sentinel = self._make(["/safe/a"], debug=True)
        orch.handle({})
        self.assertEqual(remover.removed, [])
        self.assertFalse(sentinel.cleared)

    def test_no_roots_clears_sentinel(self):
        orch, remover, sentinel = self._make([])
        orch.handle({})
        self.assertEqual(remover.removed, [])
        self.assertTrue(sentinel.cleared)


# ---------------------------------------------------------------------------
# StopEventFilter
# ---------------------------------------------------------------------------

class TestStopEventFilter(unittest.TestCase):
    def test_always_handles(self):
        self.assertTrue(StopEventFilter().should_handle({}))
        self.assertTrue(StopEventFilter().should_handle({"transcript_path": ""}))


# ---------------------------------------------------------------------------
# PipelineOutputCleaner facade
# ---------------------------------------------------------------------------

class TestPipelineOutputCleaner(unittest.TestCase):
    def test_should_handle_delegates_to_filter(self):
        c = PipelineOutputCleaner(event_filter=AlwaysFilter())
        self.assertTrue(c.should_handle({}))

        c2 = PipelineOutputCleaner(event_filter=NeverFilter())
        self.assertFalse(c2.should_handle({}))

    def test_handle_delegates_to_orchestrator(self):
        orch = RecordingOrchestrator()
        c = PipelineOutputCleaner(cleanup_orchestrator=orch)
        event = {"cwd": "/p"}
        c.handle(event)
        self.assertEqual(orch.handled, [event])


# ---------------------------------------------------------------------------
# HcConfigDebugReader
# ---------------------------------------------------------------------------

class TestHcConfigDebugReader(unittest.TestCase):
    def test_uses_injected_fn(self):
        r = HcConfigDebugReader(debug_mode_fn=lambda: True)
        self.assertTrue(r.is_debug())

        r2 = HcConfigDebugReader(debug_mode_fn=lambda: False)
        self.assertFalse(r2.is_debug())


if __name__ == "__main__":
    unittest.main()
