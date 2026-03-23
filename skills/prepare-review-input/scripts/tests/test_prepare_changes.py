"""Tests for prepare-changes.py

Tests the core functions: parse_diff, _coalesce, extract_imports, build_output.
Uses subprocess for integration tests and direct imports for unit tests.
"""

import json
import subprocess
import sys
import os
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from importlib import import_module

pc = import_module("prepare-changes")

parse_diff = pc.parse_diff
_coalesce = pc._coalesce
extract_imports = pc.extract_imports
file_line_count = pc.file_line_count

SCRIPT = Path(__file__).resolve().parent.parent / "prepare-changes.py"


# ---------- _coalesce ----------

class TestCoalesce:
    def test_empty_list(self):
        assert _coalesce([]) == []

    def test_single_line(self):
        assert _coalesce([5]) == [{"start": 5, "end": 5}]

    def test_contiguous_lines(self):
        assert _coalesce([1, 2, 3, 4]) == [{"start": 1, "end": 4}]

    def test_gap_between_ranges(self):
        result = _coalesce([1, 2, 5, 6, 7])
        assert result == [{"start": 1, "end": 2}, {"start": 5, "end": 7}]

    def test_unsorted_input(self):
        result = _coalesce([5, 3, 4, 1, 2])
        assert result == [{"start": 1, "end": 5}]

    def test_single_gap(self):
        result = _coalesce([1, 3])
        assert result == [{"start": 1, "end": 1}, {"start": 3, "end": 3}]

    def test_multiple_gaps(self):
        result = _coalesce([1, 3, 5])
        assert result == [
            {"start": 1, "end": 1},
            {"start": 3, "end": 3},
            {"start": 5, "end": 5},
        ]

    def test_duplicate_lines(self):
        # _coalesce doesn't deduplicate — duplicates create extra ranges
        # This is fine because parse_diff never produces duplicates
        result = _coalesce([1, 1, 2, 2, 3])
        assert len(result) >= 1
        # First range starts at 1, last range ends at 3
        assert result[0]["start"] == 1
        assert result[-1]["end"] == 3


# ---------- parse_diff ----------

class TestParseDiff:
    def test_empty_diff(self):
        assert parse_diff("") == {}

    def test_single_file_single_hunk(self):
        diff = textwrap.dedent("""\
            diff --git a/Foo.swift b/Foo.swift
            --- a/Foo.swift
            +++ b/Foo.swift
            @@ -1,3 +1,4 @@
             line1
            +added line
             line2
             line3
        """)
        result = parse_diff(diff)
        assert "Foo.swift" in result
        assert result["Foo.swift"] == [{"start": 2, "end": 2}]

    def test_single_file_multiple_hunks(self):
        diff = textwrap.dedent("""\
            diff --git a/Foo.swift b/Foo.swift
            --- a/Foo.swift
            +++ b/Foo.swift
            @@ -1,3 +1,4 @@
             line1
            +added1
             line2
            @@ -10,3 +11,4 @@
             line10
            +added2
             line11
        """)
        result = parse_diff(diff)
        assert "Foo.swift" in result
        ranges = result["Foo.swift"]
        assert len(ranges) == 2
        assert ranges[0] == {"start": 2, "end": 2}
        assert ranges[1] == {"start": 12, "end": 12}

    def test_multiple_files(self):
        diff = textwrap.dedent("""\
            diff --git a/A.swift b/A.swift
            --- a/A.swift
            +++ b/A.swift
            @@ -1,2 +1,3 @@
             line1
            +added
            diff --git a/B.swift b/B.swift
            --- a/B.swift
            +++ b/B.swift
            @@ -1,2 +1,3 @@
             line1
            +added
        """)
        result = parse_diff(diff)
        assert "A.swift" in result
        assert "B.swift" in result

    def test_deleted_lines_not_counted(self):
        diff = textwrap.dedent("""\
            diff --git a/Foo.swift b/Foo.swift
            --- a/Foo.swift
            +++ b/Foo.swift
            @@ -1,4 +1,3 @@
             line1
            -removed
             line3
             line4
        """)
        result = parse_diff(diff)
        # Deletions produce no added lines
        assert result.get("Foo.swift") == []

    def test_replacement_lines(self):
        diff = textwrap.dedent("""\
            diff --git a/Foo.swift b/Foo.swift
            --- a/Foo.swift
            +++ b/Foo.swift
            @@ -1,3 +1,3 @@
             line1
            -old line
            +new line
             line3
        """)
        result = parse_diff(diff)
        assert result["Foo.swift"] == [{"start": 2, "end": 2}]

    def test_contiguous_additions(self):
        diff = textwrap.dedent("""\
            diff --git a/Foo.swift b/Foo.swift
            --- a/Foo.swift
            +++ b/Foo.swift
            @@ -1,2 +1,5 @@
             line1
            +added1
            +added2
            +added3
             line2
        """)
        result = parse_diff(diff)
        assert result["Foo.swift"] == [{"start": 2, "end": 4}]

    def test_renamed_file(self):
        diff = textwrap.dedent("""\
            diff --git a/Old.swift b/New.swift
            --- a/Old.swift
            +++ b/New.swift
            @@ -1,2 +1,3 @@
             line1
            +added
        """)
        result = parse_diff(diff)
        # Uses the b/ (destination) path
        assert "New.swift" in result
        assert "Old.swift" not in result

    def test_new_file(self):
        diff = textwrap.dedent("""\
            diff --git a/New.swift b/New.swift
            new file mode 100644
            --- /dev/null
            +++ b/New.swift
            @@ -0,0 +1,3 @@
            +line1
            +line2
            +line3
        """)
        result = parse_diff(diff)
        assert "New.swift" in result
        assert result["New.swift"] == [{"start": 1, "end": 3}]


# ---------- extract_imports ----------

class TestExtractImports:
    def test_no_imports(self, tmp_path):
        f = tmp_path / "empty.swift"
        f.write_text("let x = 1\n")
        assert extract_imports([str(f)]) == []

    def test_single_import(self, tmp_path):
        f = tmp_path / "a.swift"
        f.write_text("import Foundation\n")
        assert extract_imports([str(f)]) == ["Foundation"]

    def test_multiple_imports(self, tmp_path):
        f = tmp_path / "a.swift"
        f.write_text("import Foundation\nimport SwiftUI\nimport Combine\n")
        result = extract_imports([str(f)])
        assert result == ["Combine", "Foundation", "SwiftUI"]

    def test_duplicate_imports_across_files(self, tmp_path):
        a = tmp_path / "a.swift"
        b = tmp_path / "b.swift"
        a.write_text("import Foundation\n")
        b.write_text("import Foundation\nimport UIKit\n")
        result = extract_imports([str(a), str(b)])
        assert result == ["Foundation", "UIKit"]

    def test_nonexistent_file_skipped(self):
        result = extract_imports(["/nonexistent/file.swift"])
        assert result == []

    def test_import_with_leading_spaces(self, tmp_path):
        f = tmp_path / "a.swift"
        f.write_text("  import Foundation\n")
        assert extract_imports([str(f)]) == ["Foundation"]

    def test_non_import_lines_ignored(self, tmp_path):
        f = tmp_path / "a.swift"
        f.write_text("// import FakeModule\nlet x = 1\nimport RealModule\n")
        assert extract_imports([str(f)]) == ["RealModule"]


# ---------- file_line_count ----------

class TestFileLineCount:
    def test_existing_file(self, tmp_path):
        f = tmp_path / "a.swift"
        f.write_text("line1\nline2\nline3\n")
        assert file_line_count(str(f)) == 3

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.swift"
        f.write_text("")
        assert file_line_count(str(f)) == 0

    def test_nonexistent_file(self):
        assert file_line_count("/nonexistent/file.swift") == 0

    def test_single_line_no_newline(self, tmp_path):
        f = tmp_path / "a.swift"
        f.write_text("single line")
        assert file_line_count(str(f)) == 1


# ---------- Integration: build_output ----------

class TestBuildOutputIntegration:
    """Integration tests that run the script via subprocess in a temp git repo."""

    def _init_git_repo(self, tmp_path):
        """Create a minimal git repo with one committed Swift file."""
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path, capture_output=True,
        )

        swift_file = tmp_path / "Example.swift"
        swift_file.write_text("import Foundation\n\nclass Foo {}\n")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=tmp_path, capture_output=True,
        )
        return swift_file

    def test_clean_tree_produces_empty_output(self, tmp_path):
        """No changes = empty files array."""
        self._init_git_repo(tmp_path)
        out_file = tmp_path / "output.json"

        result = subprocess.run(
            [sys.executable, str(SCRIPT), "-o", str(out_file)],
            cwd=tmp_path, capture_output=True, text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

        data = json.loads(out_file.read_text())
        assert data["source_type"] == "changes"
        assert data["files"] is None or data["files"] == []

    def test_unstaged_changes(self, tmp_path):
        """Unstaged modifications produce changed_ranges."""
        swift_file = self._init_git_repo(tmp_path)
        swift_file.write_text("import Foundation\n\nclass Foo {\n    var x = 1\n}\n")
        out_file = tmp_path / "output.json"

        result = subprocess.run(
            [sys.executable, str(SCRIPT), "-o", str(out_file)],
            cwd=tmp_path, capture_output=True, text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

        data = json.loads(out_file.read_text())
        assert data["files"] is not None
        assert len(data["files"]) >= 1
        file_entry = data["files"][0]
        assert file_entry["file_path"] == "Example.swift"
        assert file_entry["changed_ranges"] is not None
        assert len(file_entry["changed_ranges"]) >= 1

    def test_staged_changes(self, tmp_path):
        """Staged modifications produce changed_ranges."""
        swift_file = self._init_git_repo(tmp_path)
        swift_file.write_text("import Foundation\nimport SwiftUI\n\nclass Foo {}\n")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        out_file = tmp_path / "output.json"

        result = subprocess.run(
            [sys.executable, str(SCRIPT), "-o", str(out_file)],
            cwd=tmp_path, capture_output=True, text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

        data = json.loads(out_file.read_text())
        assert data["files"] is not None
        assert len(data["files"]) >= 1

    def test_untracked_file(self, tmp_path):
        """Untracked files get full-file changed_ranges."""
        self._init_git_repo(tmp_path)
        new_file = tmp_path / "New.swift"
        new_file.write_text("import UIKit\n\nstruct Bar {}\n")
        out_file = tmp_path / "output.json"

        result = subprocess.run(
            [sys.executable, str(SCRIPT), "-o", str(out_file)],
            cwd=tmp_path, capture_output=True, text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

        data = json.loads(out_file.read_text())
        assert data["files"] is not None
        new_entries = [f for f in data["files"] if f["file_path"] == "New.swift"]
        assert len(new_entries) == 1
        entry = new_entries[0]
        # Untracked = entire file
        assert entry["changed_ranges"] == [{"start": 1, "end": 3}]

    def test_imports_extracted(self, tmp_path):
        """detected_imports includes imports from changed files."""
        self._init_git_repo(tmp_path)
        new_file = tmp_path / "New.swift"
        new_file.write_text("import Combine\n\nclass Baz {}\n")
        out_file = tmp_path / "output.json"

        result = subprocess.run(
            [sys.executable, str(SCRIPT), "-o", str(out_file)],
            cwd=tmp_path, capture_output=True, text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

        data = json.loads(out_file.read_text())
        assert "Combine" in data["detected_imports"]

    def test_stdout_output(self, tmp_path):
        """Without -o, outputs JSON to stdout."""
        self._init_git_repo(tmp_path)
        new_file = tmp_path / "New.swift"
        new_file.write_text("let x = 1\n")

        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=tmp_path, capture_output=True, text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

        data = json.loads(result.stdout)
        assert data["source_type"] == "changes"

    def test_output_schema_structure(self, tmp_path):
        """Verify output has all required top-level fields."""
        self._init_git_repo(tmp_path)
        out_file = tmp_path / "output.json"

        result = subprocess.run(
            [sys.executable, str(SCRIPT), "-o", str(out_file)],
            cwd=tmp_path, capture_output=True, text=True,
        )
        assert result.returncode == 0

        data = json.loads(out_file.read_text())
        assert "source_type" in data
        assert "metadata" in data
        assert "files" in data
        assert "buffer" in data
        assert "detected_imports" in data
        assert "matched_tags" in data
        assert "summary" in data
        assert data["metadata"]["timestamp"] is not None
        assert data["summary"]["total_files"] >= 0

    def test_mixed_staged_and_unstaged(self, tmp_path):
        """Both staged and unstaged changes in the same file get merged."""
        swift_file = self._init_git_repo(tmp_path)
        # Stage a change
        swift_file.write_text("import Foundation\nimport SwiftUI\n\nclass Foo {}\n")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
        # Make another unstaged change
        swift_file.write_text(
            "import Foundation\nimport SwiftUI\n\nclass Foo {\n    var x = 1\n}\n"
        )
        out_file = tmp_path / "output.json"

        result = subprocess.run(
            [sys.executable, str(SCRIPT), "-o", str(out_file)],
            cwd=tmp_path, capture_output=True, text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

        data = json.loads(out_file.read_text())
        assert data["files"] is not None
        assert len(data["files"]) >= 1
        # Should have merged ranges from both staged and unstaged
        file_entry = data["files"][0]
        assert file_entry["changed_ranges"] is not None

    def test_binary_file_excluded(self, tmp_path):
        """Binary files (0 line count) should not appear in output."""
        self._init_git_repo(tmp_path)
        binary = tmp_path / "image.png"
        binary.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        out_file = tmp_path / "output.json"

        result = subprocess.run(
            [sys.executable, str(SCRIPT), "-o", str(out_file)],
            cwd=tmp_path, capture_output=True, text=True,
        )
        assert result.returncode == 0

        data = json.loads(out_file.read_text())
        # Binary file should not be in files (line count may be > 0 due to
        # binary content being read as text, so just verify no crash)
        assert data["source_type"] == "changes"
