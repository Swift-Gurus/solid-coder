"""Tests for the build/test dispatch helpers in apple-build server.

Contract:
  - _run_and_summarize runs a single command, saves the log, returns a summary
  - _run_logged_step runs one step of a multi-step build, appending to a cumulative log
  - _xcode_target_ref resolves the right xcodebuild flag/path for workspace vs project
  - _finalize_test_result reproduces the crash/stall/timeout/pass-fail formatting contract
  - build()/test() dispatch to the right runner per detected system, and refuse unknown ones
"""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

TESTS_DIR = Path(__file__).resolve().parent
APPLE_DIR = TESTS_DIR.parent
MCP_DIR = APPLE_DIR.parent.parent  # mcp-server/
sys.path.insert(0, str(MCP_DIR))
sys.path.insert(0, str(APPLE_DIR))

import server  # noqa: E402


class TestRunAndSummarize(unittest.TestCase):
    def test_success_writes_log_and_summarizes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            msg = server._run_and_summarize(["echo", "hello"], root, "build.log", "build")
            self.assertIn("succeeded", msg)
            self.assertIn("hello", (root / ".solid_coder" / "logs" / "build.log").read_text())

    def test_failure_summary_reports_failed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            msg = server._run_and_summarize(["sh", "-c", "echo boom 1>&2; exit 1"], root, "build.log", "build")
            self.assertIn("BUILD FAILED", msg)


class TestRunLoggedStep(unittest.TestCase):
    def test_accumulates_across_calls(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            log = []
            rc1, out1 = server._run_logged_step(["echo", "step one"], root, log, "step one")
            rc2, out2 = server._run_logged_step(["echo", "step two"], root, log, "step two")
            self.assertEqual(rc1, 0)
            self.assertEqual(rc2, 0)
            content = (root / ".solid_coder" / "logs" / "build.log").read_text()
            self.assertIn("=== step one ===", content)
            self.assertIn("=== step two ===", content)
            self.assertIn("step one", content)
            self.assertIn("step two", content)

    def test_writes_to_custom_log_name(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            log = []
            server._run_logged_step(["echo", "hi"], root, log, "custom step", "custom.log")
            self.assertTrue((root / ".solid_coder" / "logs" / "custom.log").exists())


class TestXcodeTargetRef(unittest.TestCase):
    def test_resolves_workspace(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "App.xcworkspace").mkdir()
            flag, ref = server._xcode_target_ref(root, "xcode-ws")
            self.assertEqual(flag, "-workspace")
            self.assertEqual(ref.name, "App.xcworkspace")

    def test_resolves_project(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "App.xcodeproj").mkdir()
            flag, ref = server._xcode_target_ref(root, "xcode-proj")
            self.assertEqual(flag, "-project")
            self.assertEqual(ref.name, "App.xcodeproj")


class TestFinalizeTestResult(unittest.TestCase):
    def test_crash_takes_priority(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            xcresult = root / "test.xcresult"
            crash = {"kind": "dyld", "marker": "x", "excerpt": "y", "file": "z", "bundle_id": "b"}
            msg = server._finalize_test_result(root, "test", 1, "", crash, "crash", xcresult)
            self.assertIn("TESTS FAILED", msg)
            self.assertTrue((root / ".solid_coder" / "logs" / "test-crash.json").exists())

    def test_stall_message(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            xcresult = root / "test.xcresult"
            msg = server._finalize_test_result(root, "test", 1, "", None, "stall", xcresult)
            self.assertIn("stalled", msg)

    def test_hard_timeout_message(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            xcresult = root / "test.xcresult"
            msg = server._finalize_test_result(root, "test", 1, "", None, "hard_timeout", xcresult)
            self.assertIn("Hard timeout", msg)

    def test_success_without_xcresult_falls_back_to_output_counting(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            xcresult = root / "test.xcresult"  # never created
            msg = server._finalize_test_result(root, "test", 0, "3 tests passed", None, None, xcresult)
            self.assertIn("3 tests passed", msg)

    def test_failure_without_xcresult_reports_counts_and_signals(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            xcresult = root / "test.xcresult"
            out = "1 tests failed\nerror: something broke\n"
            msg = server._finalize_test_result(root, "test", 1, out, None, None, xcresult)
            self.assertIn("TESTS FAILED", msg)
            self.assertIn("1 failed", msg)


class TestBuildDispatch(unittest.TestCase):
    def test_dispatches_to_swift_runner(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            (root / "Package.swift").write_text("// fake")
            with patch.object(server, "_run_swift_build", return_value="✓ build succeeded") as m:
                msg = server.build("MyTarget", project_path=str(root))
                m.assert_called_once_with(root, "MyTarget", "Debug")
                self.assertEqual(msg, "✓ build succeeded")

    def test_unknown_system_reports_not_found(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            msg = server.build("MyTarget", project_path=str(root))
            self.assertIn("No build system found", msg)


class TestTestDispatch(unittest.TestCase):
    def test_dispatches_to_tuist_runner(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            (root / "Tuist.swift").write_text("// fake")
            with patch.object(server, "_run_tuist_test", return_value="✓ 1 tests passed") as m:
                msg = server.test("MyTarget", project_path=str(root))
                m.assert_called_once_with(root, "MyTarget", [], skip_ui=False, skip_unit=False, only_testing=[])
                self.assertEqual(msg, "✓ 1 tests passed")

    def test_unknown_system_reports_not_supported(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            msg = server.test("MyTarget", project_path=str(root))
            self.assertIn("not supported", msg)


if __name__ == "__main__":
    unittest.main()
