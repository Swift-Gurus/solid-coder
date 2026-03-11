"""Tests for load-reference.py"""

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "load-reference.py"


def _run(*args):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True,
    )
    return result


class TestStripFrontmatter:
    def test_strips_frontmatter(self, tmp_path):
        md = tmp_path / "rule.md"
        md.write_text("---\nname: srp\ncategory: solid\n---\n\n# Title\n\nBody.")
        result = _run(str(md))
        assert result.returncode == 0
        assert "---" not in result.stdout.split("===")[-1].split("# Title")[0]
        assert "name: srp" not in result.stdout
        assert "# Title" in result.stdout
        assert "Body." in result.stdout

    def test_no_frontmatter_passes_through(self, tmp_path):
        f = tmp_path / "example.swift"
        f.write_text("class Foo {\n    func bar() {}\n}")
        result = _run(str(f))
        assert result.returncode == 0
        assert "class Foo" in result.stdout
        assert "func bar" in result.stdout

    def test_header_shows_absolute_path(self, tmp_path):
        md = tmp_path / "rule.md"
        md.write_text("---\nname: test\n---\n# Body")
        result = _run(str(md))
        assert result.returncode == 0
        assert f"=== {md.resolve()} ===" in result.stdout


class TestDirectoryExpansion:
    def test_expands_directory(self, tmp_path):
        d = tmp_path / "Examples"
        d.mkdir()
        (d / "a.swift").write_text("// a")
        (d / "b.swift").write_text("// b")
        result = _run(str(d))
        assert result.returncode == 0
        assert "// a" in result.stdout
        assert "// b" in result.stdout
        assert result.stdout.count("===") == 4  # 2 files × 2 (open + close)

    def test_empty_directory(self, tmp_path):
        d = tmp_path / "Empty"
        d.mkdir()
        result = _run(str(d))
        assert result.returncode == 1
        assert "no files found" in result.stderr.lower()


class TestMultipleInputs:
    def test_multiple_files(self, tmp_path):
        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"
        f1.write_text("---\nname: a\n---\n# A")
        f2.write_text("---\nname: b\n---\n# B")
        result = _run(str(f1), str(f2))
        assert result.returncode == 0
        assert "# A" in result.stdout
        assert "# B" in result.stdout
        assert "name: a" not in result.stdout
        assert "name: b" not in result.stdout

    def test_mixed_files_and_dirs(self, tmp_path):
        f = tmp_path / "rule.md"
        f.write_text("---\nname: rule\n---\n# Rule")
        d = tmp_path / "Examples"
        d.mkdir()
        (d / "ex.swift").write_text("// example")
        result = _run(str(f), str(d))
        assert result.returncode == 0
        assert "# Rule" in result.stdout
        assert "// example" in result.stdout


class TestErrorCases:
    def test_no_arguments(self):
        result = _run()
        assert result.returncode == 1
        assert "usage" in result.stderr.lower()

    def test_nonexistent_path(self, tmp_path):
        result = _run(str(tmp_path / "nope.md"))
        assert result.returncode == 1
        assert "warning" in result.stderr.lower() or "no files" in result.stderr.lower()

    def test_skips_missing_with_warning(self, tmp_path):
        f = tmp_path / "exists.md"
        f.write_text("# Real file")
        result = _run(str(tmp_path / "nope.md"), str(f))
        assert result.returncode == 0
        assert "warning" in result.stderr.lower()
        assert "# Real file" in result.stdout
