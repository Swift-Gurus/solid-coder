"""Tests for mcp-server/build/apple/server.py — autodiscovery and output parsing."""
import sys
import tempfile
import unittest
from pathlib import Path

# Import the server module directly (not via subprocess) for unit testing
SERVER = Path(__file__).resolve().parents[2] / "mcp-server" / "build" / "apple" / "server.py"
sys.path.insert(0, str(SERVER.parent.parent.parent / "mcp-server"))  # protocol.py
sys.path.insert(0, str(SERVER.parent))
import importlib.util
spec = importlib.util.spec_from_file_location("apple_server", SERVER)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class TestAutodiscovery(unittest.TestCase):
    def test_tuist_detected_by_tuist_swift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Tuist.swift").write_text("// tuist")
            system, found = mod._find_project_root(root)
            self.assertEqual(system, "tuist")
            self.assertEqual(found, root.resolve())

    def test_xcworkspace_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "MyApp.xcworkspace").mkdir()
            system, found = mod._find_project_root(root)
            self.assertEqual(system, "xcodebuild-workspace")

    def test_xcodeproj_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "MyApp.xcodeproj").mkdir()
            system, found = mod._find_project_root(root)
            self.assertEqual(system, "xcodebuild-project")

    def test_swift_package_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Package.swift").write_text("// spm")
            system, found = mod._find_project_root(root)
            self.assertEqual(system, "swift")

    def test_tuist_takes_priority_over_xcworkspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Tuist.swift").write_text("// tuist")
            (root / "MyApp.xcworkspace").mkdir()
            system, _ = mod._find_project_root(root)
            self.assertEqual(system, "tuist")

    def test_discovers_from_subdirectory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Tuist.swift").write_text("// tuist")
            subdir = root / "Packages" / "MyFeature" / "Sources"
            subdir.mkdir(parents=True)
            system, found = mod._find_project_root(subdir)
            self.assertEqual(system, "tuist")
            self.assertEqual(found, root.resolve())

    def test_unknown_when_nothing_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            system, _ = mod._find_project_root(Path(tmp))
            self.assertEqual(system, "unknown")

    def test_tq_detected_when_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Tuist.swift").write_text("// tuist")
            tq_dir = root / "Tuist" / "scripts"
            tq_dir.mkdir(parents=True)
            (tq_dir / "tq").write_text("#!/bin/bash\ntuist $@")
            system, found = mod._find_project_root(root)
            self.assertEqual(system, "tuist")
            self.assertTrue((found / "Tuist" / "scripts" / "tq").is_file())


class TestOutputFiltering(unittest.TestCase):
    def test_keeps_error_lines(self):
        output = "/path/Foo.swift:12:5: error: cannot convert value"
        result = mod._filter_output(output)
        self.assertIn("error:", result)
        self.assertIn("Foo.swift", result)

    def test_keeps_warning_lines(self):
        output = "/path/Bar.swift:5:1: warning: unused variable 'x'"
        result = mod._filter_output(output)
        self.assertIn("warning:", result)

    def test_keeps_build_failed(self):
        output = "Compiling...\n** BUILD FAILED **\nSome noise"
        result = mod._filter_output(output)
        self.assertIn("BUILD FAILED", result)
        self.assertNotIn("Compiling", result)
        self.assertNotIn("Some noise", result)

    def test_drops_noise_lines(self):
        output = "** BUILD SUCCEEDED **\nCompiling Swift sources\nLinking"
        result = mod._filter_output(output)
        self.assertEqual(result, "")

    def test_keeps_tuist_error_prefix(self):
        output = "[x] Foo.swift:1:1: error: something broke"
        result = mod._filter_output(output)
        self.assertIn("[x]", result)

    def test_empty_output_returns_empty(self):
        self.assertEqual(mod._filter_output(""), "")


class TestDetectBuildSystemTool(unittest.TestCase):
    def test_returns_system_and_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Tuist.swift").write_text("// tuist")
            result = mod.detect_build_system(project_path=str(root))
            self.assertEqual(result["system"], "tuist")
            self.assertEqual(result["root"], str(root.resolve()))
            self.assertIn("example_command", result)

    def test_reports_tq_presence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Tuist.swift").write_text("// tuist")
            tq_dir = root / "Tuist" / "scripts"
            tq_dir.mkdir(parents=True)
            (tq_dir / "tq").write_text("#!/bin/bash")
            result = mod.detect_build_system(project_path=str(root))
            self.assertTrue(result["has_tq"])

    def test_unknown_for_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = mod.detect_build_system(project_path=tmp)
            self.assertEqual(result["system"], "unknown")


if __name__ == "__main__":
    unittest.main()
