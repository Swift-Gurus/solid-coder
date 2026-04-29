"""Tests for the crash-detection watchdog in apple-build server.

Contract:
  - _scan_for_crash returns a structured dict for known crash markers, None otherwise
  - _classify_crash bins markers into dyld / memory / signal / unknown
  - _format_crash_response produces a deterministic LLM-facing message
  - _save_crash_info / _clear_crash_info round-trip via JSON
  - _run_with_watchdog kills the process tree on crash detection (Tier 1)
  - _run_with_watchdog kills the process tree on stall (Tier 2)
  - get_log prepends crash info when <kind>-crash.json exists
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

# Import server module directly for unit-level tests
TESTS_DIR = Path(__file__).resolve().parent
APPLE_DIR = TESTS_DIR.parent
MCP_DIR = APPLE_DIR.parent.parent  # mcp-server/
sys.path.insert(0, str(MCP_DIR))
sys.path.insert(0, str(APPLE_DIR))

import server  # noqa: E402

# Real fixture: a dyld error captured from a real ui-test run on claude-code-inspector.
# Self-contained — does not depend on the original project being on disk.
DYLD_ERROR_TEXT = """Standard output and standard error from com.example.testapp with process ID 12345 beginning at 2026-04-29 00:49:51 +0000

dyld[12345]: Library not loaded: @rpath/Testing.framework/Versions/A/Testing
  Referenced from: <CD4290EE-4362-3FCB-AEC4-9401244ECA26> /Users/foo/DerivedData/Build/Products/Debug/UnitTestConveniences.framework/Versions/A/UnitTestConveniences
  Reason: tried: '/Users/foo/DerivedData/Build/Products/Debug/Testing.framework/Versions/A/Testing' (no such file), '/usr/lib/swift/Testing.framework/Versions/A/Testing' (no such file, not in dyld cache)
"""

EXC_BAD_ACCESS_TEXT = """Process 99999 stopped
Thread 0 Crashed:
EXC_BAD_ACCESS (code=1, address=0x0)
0   libsystem_c.dylib    0x000000018a4c1234 strlen + 16
1   TestApp              0x0000000100008abc -[Foo bar] + 44
"""

SIGABRT_TEXT = """*** Terminating app due to uncaught exception 'NSInvalidArgumentException'
signal SIGABRT
Stack:
0   CoreFoundation       0x000000018b2d0000 __exceptionPreprocess + 220
"""

CLEAN_OUTPUT = """Test Suite 'All tests' started.
    ✔ "First test" (0.001s)
Test Suite 'All tests' passed.
"""


def make_xcresult_with_text(parent: Path, bundle_id: str, text: str) -> Path:
    """Build a minimal xcresult-shaped directory with one StandardOutputAndStandardError file."""
    xcr = parent / "test.xcresult"
    diag = xcr / "Staging" / "1_Test" / "Diagnostics" / "Foo-AAAA"
    diag.mkdir(parents=True, exist_ok=True)
    (diag / f"StandardOutputAndStandardError-{bundle_id}.txt").write_text(text, encoding="utf-8")
    return xcr


class TestScanForCrash(unittest.TestCase):
    def test_returns_none_when_xcresult_missing(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertIsNone(server._scan_for_crash(Path(td) / "no-such.xcresult"))

    def test_returns_none_when_no_crash_file(self):
        with tempfile.TemporaryDirectory() as td:
            xcr = Path(td) / "test.xcresult"
            (xcr / "Staging").mkdir(parents=True)
            self.assertIsNone(server._scan_for_crash(xcr))

    def test_returns_none_for_clean_output(self):
        with tempfile.TemporaryDirectory() as td:
            xcr = make_xcresult_with_text(Path(td), "com.example.app", CLEAN_OUTPUT)
            self.assertIsNone(server._scan_for_crash(xcr))

    def test_detects_dyld_error(self):
        with tempfile.TemporaryDirectory() as td:
            xcr = make_xcresult_with_text(Path(td), "com.example.testapp", DYLD_ERROR_TEXT)
            info = server._scan_for_crash(xcr)
            self.assertIsNotNone(info)
            self.assertEqual(info["kind"], "dyld")
            self.assertEqual(info["bundle_id"], "com.example.testapp")
            self.assertIn("Library not loaded", info["excerpt"])
            self.assertIn("Testing.framework", info["excerpt"])
            self.assertTrue(info["file"].endswith("StandardOutputAndStandardError-com.example.testapp.txt"))

    def test_detects_exc_bad_access(self):
        with tempfile.TemporaryDirectory() as td:
            xcr = make_xcresult_with_text(Path(td), "com.example.app", EXC_BAD_ACCESS_TEXT)
            info = server._scan_for_crash(xcr)
            self.assertIsNotNone(info)
            self.assertEqual(info["kind"], "memory")
            self.assertIn("EXC_BAD_ACCESS", info["excerpt"])

    def test_detects_sigabrt(self):
        with tempfile.TemporaryDirectory() as td:
            xcr = make_xcresult_with_text(Path(td), "com.example.app", SIGABRT_TEXT)
            info = server._scan_for_crash(xcr)
            self.assertIsNotNone(info)
            self.assertEqual(info["kind"], "signal")

    def test_iterates_multiple_files_finds_first_crash(self):
        with tempfile.TemporaryDirectory() as td:
            xcr = make_xcresult_with_text(Path(td), "com.example.clean", CLEAN_OUTPUT)
            diag2 = xcr / "Staging" / "1_Test" / "Diagnostics" / "Bar-BBBB"
            diag2.mkdir(parents=True)
            (diag2 / "StandardOutputAndStandardError-com.example.crashy.txt").write_text(DYLD_ERROR_TEXT)
            info = server._scan_for_crash(xcr)
            self.assertIsNotNone(info)
            self.assertEqual(info["bundle_id"], "com.example.crashy")


class TestClassifyCrash(unittest.TestCase):
    def test_dyld_classification(self):
        self.assertEqual(server._classify_crash("dyld[42]: Library not loaded: foo"), "dyld")
        self.assertEqual(server._classify_crash("Symbol not found: _foo"), "dyld")

    def test_memory_classification(self):
        self.assertEqual(server._classify_crash("EXC_BAD_ACCESS (code=1)"), "memory")
        self.assertEqual(server._classify_crash("signal SIGSEGV"), "memory")
        self.assertEqual(server._classify_crash("EXC_BAD_INSTRUCTION"), "memory")

    def test_signal_classification(self):
        self.assertEqual(server._classify_crash("signal SIGABRT"), "signal")
        self.assertEqual(server._classify_crash("Crashed Thread: 0"), "signal")

    def test_unknown_falls_through(self):
        self.assertEqual(server._classify_crash("some random text"), "unknown")


class TestFormatCrashResponse(unittest.TestCase):
    def _info(self):
        return {
            "kind": "dyld",
            "marker": "Library not loaded:",
            "excerpt": "dyld[42]: Library not loaded: @rpath/Testing.framework\n  Referenced from: foo",
            "file": "/tmp/test.xcresult/Staging/.../StandardOutputAndStandardError-com.example.app.txt",
            "bundle_id": "com.example.app",
        }

    def test_message_contains_required_fields(self):
        msg = server._format_crash_response(self._info(), "crash", "ui-test")
        self.assertIn("** TESTS FAILED **", msg)
        self.assertIn("missing framework", msg.lower())
        self.assertIn("dyld", msg)
        self.assertIn("com.example.app", msg)
        self.assertIn("Library not loaded:", msg)
        self.assertIn("get_log(kind=\"ui-test\")", msg)

    def test_stall_kill_reason_appended(self):
        msg = server._format_crash_response(self._info(), "stall", "ui-test")
        self.assertIn("stall watchdog", msg)

    def test_normal_crash_no_stall_note(self):
        msg = server._format_crash_response(self._info(), "crash", "ui-test")
        self.assertNotIn("stall watchdog", msg)


class TestSaveAndClearCrashInfo(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            info = {"kind": "dyld", "marker": "Library not loaded:", "excerpt": "foo",
                    "file": "/tmp/x.txt", "bundle_id": "com.example.app"}
            p = server._save_crash_info(root, "ui-test", info)
            self.assertTrue(p.exists())
            loaded = json.loads(p.read_text())
            self.assertEqual(loaded, info)
            server._clear_crash_info(root, "ui-test")
            self.assertFalse(p.exists())

    def test_clear_when_missing_is_noop(self):
        with tempfile.TemporaryDirectory() as td:
            server._clear_crash_info(Path(td), "ui-test")  # must not raise


class TestGetLogIncludesCrash(unittest.TestCase):
    def _setup_logs(self, td: Path, kind: str, with_crash: bool):
        logs = td / ".solid_coder" / "logs"
        logs.mkdir(parents=True)
        (logs / f"{kind}.log").write_text("=== tuist test ===\nfoo\nbar\n", encoding="utf-8")
        if with_crash:
            (logs / f"{kind}-crash.json").write_text(json.dumps({
                "kind": "dyld",
                "marker": "Library not loaded:",
                "excerpt": "dyld[42]: Library not loaded: @rpath/X.framework",
                "file": str(logs / "ui-test.xcresult" / "stuff.txt"),
                "bundle_id": "com.example.app",
            }), encoding="utf-8")
        return logs

    def test_get_log_without_crash_returns_log_only(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            self._setup_logs(tdp, "ui-test", with_crash=False)
            # Force _detect to return our temp dir as the root
            (tdp / "Tuist.swift").write_text("// fake")
            out = server.get_log(kind="ui-test", project_path=str(tdp))
            self.assertNotIn("Crash detected", out)
            self.assertIn("foo", out)
            self.assertIn("bar", out)

    def test_get_log_with_crash_prepends_crash_section(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            self._setup_logs(tdp, "ui-test", with_crash=True)
            (tdp / "Tuist.swift").write_text("// fake")
            out = server.get_log(kind="ui-test", project_path=str(tdp))
            self.assertIn("=== Crash detected during run ===", out)
            self.assertIn("Library not loaded:", out)
            self.assertIn("com.example.app", out)
            # Ordering: crash section before raw log
            self.assertLess(out.index("=== Crash detected"), out.index("=== tuist test"))


class TestWatchdogIntegration(unittest.TestCase):
    """Light integration tests for _run_with_watchdog. Avoid running real tuist/xcodebuild."""

    def test_clean_run_returns_normally(self):
        with tempfile.TemporaryDirectory() as td:
            xcr = Path(td) / "test.xcresult"  # never created — that's fine for "no crash" path
            rc, out, crash, kill = server._run_with_watchdog(
                ["echo", "hello world"], Path(td), xcr,
                hard_timeout=10, stall_timeout=10, crash_poll=0.5,
            )
            self.assertEqual(rc, 0)
            self.assertIn("hello world", out)
            self.assertIsNone(crash)
            self.assertIsNone(kill)

    def test_crash_detection_triggers_kill(self):
        """Spawn a sleep, drop a crash file, verify watchdog detects it and kills the process."""
        with tempfile.TemporaryDirectory() as td:
            xcr = make_xcresult_with_text(Path(td), "com.example.testapp", DYLD_ERROR_TEXT)
            t0 = time.monotonic()
            rc, out, crash, kill = server._run_with_watchdog(
                ["sleep", "30"], Path(td), xcr,
                hard_timeout=20, stall_timeout=20, crash_poll=0.5,
            )
            elapsed = time.monotonic() - t0
            self.assertLess(elapsed, 10, f"Watchdog should kill within seconds, took {elapsed:.1f}s")
            self.assertEqual(kill, "crash")
            self.assertIsNotNone(crash)
            self.assertEqual(crash["kind"], "dyld")

    def test_stall_detection_kills_silent_process(self):
        with tempfile.TemporaryDirectory() as td:
            xcr = Path(td) / "test.xcresult"
            t0 = time.monotonic()
            rc, out, crash, kill = server._run_with_watchdog(
                ["sleep", "30"], Path(td), xcr,
                hard_timeout=20, stall_timeout=2, crash_poll=0.5,
            )
            elapsed = time.monotonic() - t0
            self.assertLess(elapsed, 15, f"Stall watchdog should fire ~{2}s + slack, took {elapsed:.1f}s")
            self.assertEqual(kill, "stall")
            self.assertIsNone(crash)


if __name__ == "__main__":
    unittest.main()
