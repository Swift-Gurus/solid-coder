"""Tests for mcp-server/build/apple/server.py"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "mcp-server"))
sys.path.insert(0, str(ROOT / "mcp-server" / "build" / "apple"))

import importlib.util
spec = importlib.util.spec_from_file_location(
    "apple_server", ROOT / "mcp-server" / "build" / "apple" / "server.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class TestAutodiscovery(unittest.TestCase):
    def test_tuist_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "Tuist.swift").write_text("let x = 1")
            system, root = mod._detect(Path(tmp))
            self.assertEqual(system, "tuist")
            self.assertEqual(root, Path(tmp).resolve())

    def test_xcworkspace_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "App.xcworkspace").mkdir()
            system, _ = mod._detect(Path(tmp))
            self.assertEqual(system, "xcode-ws")

    def test_xcodeproj_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "App.xcodeproj").mkdir()
            system, _ = mod._detect(Path(tmp))
            self.assertEqual(system, "xcode-proj")

    def test_swift_package_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "Package.swift").write_text("// spm")
            system, _ = mod._detect(Path(tmp))
            self.assertEqual(system, "swift")

    def test_tuist_priority_over_xcworkspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "Tuist.swift").write_text("")
            Path(tmp, "App.xcworkspace").mkdir()
            system, _ = mod._detect(Path(tmp))
            self.assertEqual(system, "tuist")

    def test_walks_up_from_subdir(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "Tuist.swift").write_text("")
            sub = Path(tmp, "Packages", "Foo", "Sources")
            sub.mkdir(parents=True)
            system, root = mod._detect(sub)
            self.assertEqual(system, "tuist")
            self.assertEqual(root, Path(tmp).resolve())

    def test_tuist_root_wins_over_subpackage_xcodeproj(self):
        """Tuist.swift at root must win over .xcodeproj in a sub-package."""
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "Tuist.swift").write_text("")
            sub = Path(tmp, "Packages", "Foo")
            sub.mkdir(parents=True)
            Path(sub, "Foo.xcodeproj").mkdir()  # xcodeproj in sub-package
            system, root = mod._detect(sub)
            self.assertEqual(system, "tuist")
            self.assertEqual(root, Path(tmp).resolve())

    def test_unknown_for_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            system, _ = mod._detect(Path(tmp))
            self.assertEqual(system, "unknown")


class TestOutputFilter(unittest.TestCase):
    def test_keeps_error_lines(self):
        out = "Foo.swift:12:5: error: type mismatch"
        self.assertIn("error:", mod._filter(out))

    def test_keeps_warning_lines(self):
        out = "Bar.swift:3:1: warning: unused variable"
        self.assertIn("warning:", mod._filter(out))

    def test_keeps_build_failed(self):
        out = "Compiling...\n** BUILD FAILED **\nDone"
        result = mod._filter(out)
        self.assertIn("BUILD FAILED", result)
        self.assertNotIn("Compiling", result)

    def test_drops_noise(self):
        out = "Build target Foo\nCompiling Swift...\nLinking"
        self.assertEqual(mod._filter(out), "")

    def test_empty_input(self):
        self.assertEqual(mod._filter(""), "")


class TestLogHelpers(unittest.TestCase):
    def test_save_and_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = mod._save(root, "build.log", "hello world")
            self.assertTrue(path.exists())
            self.assertEqual(path.read_text(), "hello world")

    def test_log_dir_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = mod._log_dir(root)
            self.assertTrue(d.exists())
            self.assertEqual(d, root / ".solid_coder" / "logs")


class TestDetectBuildSystemTool(unittest.TestCase):
    def test_returns_system_and_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "Tuist.swift").write_text("")
            result = mod.detect_build_system(project_path=tmp)
            self.assertIn("tuist", result)
            self.assertIn(str(Path(tmp).resolve()), result)
            self.assertNotIn("tq", result)
            self.assertNotIn("example_command", result)

    def test_no_client_paths_exposed(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "Tuist.swift").write_text("")
            result = mod.detect_build_system(project_path=tmp)
            # Should not contain any client-specific script paths
            self.assertNotIn("scripts/tq", result)


class TestGetLog(unittest.TestCase):
    def test_returns_log_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mod._save(root, "build.log", "line1\nline2\nline3")
            result = mod.get_log(kind="build", project_path=tmp)
            self.assertIn("line1", result)
            self.assertIn("line3", result)

    def test_tail_parameter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mod._save(root, "build.log", "a\nb\nc\nd\ne")
            result = mod.get_log(kind="build", project_path=tmp, tail=2)
            lines = result.strip().splitlines()
            self.assertEqual(lines, ["d", "e"])

    def test_missing_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = mod.get_log(kind="build", project_path=tmp)
            self.assertIn("No build.log found", result)


if __name__ == "__main__":
    unittest.main()
