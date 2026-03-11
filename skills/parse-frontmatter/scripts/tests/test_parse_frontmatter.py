"""Tests for parse-frontmatter.py"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "parse-frontmatter.py"


def _run(*args):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True,
    )
    return result


def _write_md(path, frontmatter, body="# Title\n\nBody text."):
    """Write a markdown file with YAML frontmatter."""
    lines = ["---"]
    for key, value in frontmatter.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        elif value is None:
            lines.append(f"{key}:")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    lines.append("")
    lines.append(body)
    path.write_text("\n".join(lines))


class TestNoFrontmatter:
    def test_file_without_frontmatter(self, tmp_path):
        md = tmp_path / "no-frontmatter.md"
        md.write_text("# Just a heading\n\nNo frontmatter here.")
        result = _run(str(md))
        assert result.returncode == 1
        assert "no frontmatter" in result.stderr.lower()

    def test_file_with_only_opening_delimiter(self, tmp_path):
        md = tmp_path / "broken.md"
        md.write_text("---\nname: test\nNo closing delimiter.")
        result = _run(str(md))
        assert result.returncode == 1
        assert "no frontmatter" in result.stderr.lower()


class TestMissingFile:
    def test_nonexistent_file(self, tmp_path):
        result = _run(str(tmp_path / "does-not-exist.md"))
        assert result.returncode == 1
        assert "not found" in result.stderr.lower()

    def test_no_arguments(self):
        result = _run()
        assert result.returncode == 1
        assert "usage" in result.stderr.lower()


class TestRuleComplete:
    """A complete rule.md with all fields."""

    def test_all_fields_present(self, tmp_path):
        # Mimic real layout: references/SRP/rule.md → grandparent = references/
        refs_root = tmp_path / "references"
        principle_dir = refs_root / "SRP"
        principle_dir.mkdir(parents=True)
        md = principle_dir / "rule.md"
        _write_md(md, {
            "name": "srp",
            "displayName": "Single Responsibility Principle",
            "category": "solid",
            "description": "Verb counting and cohesion group analysis",
            "required_patterns": ["structural/facade"],
        })
        (refs_root / "design_patterns" / "structural").mkdir(parents=True)
        (refs_root / "design_patterns" / "structural" / "facade.md").write_text("---\nname: facade\n---\n")

        result = _run(str(md))
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["name"] == "srp"
        assert data["displayName"] == "Single Responsibility Principle"
        assert data["category"] == "solid"
        assert data["description"] == "Verb counting and cohesion group analysis"
        assert len(data["required_patterns"]) == 1
        assert data["required_patterns"][0].endswith("structural/facade.md")

    def test_multiple_required_patterns(self, tmp_path):
        refs_root = tmp_path / "references"
        principle_dir = refs_root / "TEST"
        principle_dir.mkdir(parents=True)
        md = principle_dir / "rule.md"
        _write_md(md, {
            "name": "test",
            "displayName": "Test",
            "category": "solid",
            "description": "Test rule",
            "required_patterns": ["structural/facade", "behavioral/strategy"],
        })
        result = _run(str(md))
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert len(data["required_patterns"]) == 2
        assert any("facade.md" in p for p in data["required_patterns"])
        assert any("strategy.md" in p for p in data["required_patterns"])

    def test_refs_root_override(self, tmp_path):
        """Explicit --refs-root overrides grandparent auto-detection."""
        md = tmp_path / "rule.md"
        _write_md(md, {
            "name": "srp",
            "required_patterns": ["structural/facade"],
        })
        custom_root = tmp_path / "custom"
        custom_root.mkdir()
        result = _run(str(md), "--refs-root", str(custom_root))
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert str(custom_root) in data["required_patterns"][0]


class TestRuleMissingDescription:
    def test_no_description(self, tmp_path):
        md = tmp_path / "rule.md"
        _write_md(md, {
            "name": "srp",
            "displayName": "Single Responsibility Principle",
            "category": "solid",
        })
        result = _run(str(md))
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "description" not in data
        assert data["name"] == "srp"


class TestRuleMissingCategory:
    def test_no_category(self, tmp_path):
        md = tmp_path / "rule.md"
        _write_md(md, {
            "name": "srp",
            "displayName": "Single Responsibility Principle",
            "description": "Some description",
        })
        result = _run(str(md))
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "category" not in data
        assert data["name"] == "srp"


class TestRuleMissingDisplayName:
    def test_no_display_name(self, tmp_path):
        md = tmp_path / "rule.md"
        _write_md(md, {
            "name": "srp",
            "category": "solid",
            "description": "Some description",
        })
        result = _run(str(md))
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "displayName" not in data
        assert data["name"] == "srp"


class TestExamplesDefault:
    """examples defaults to ["Examples"] when omitted and directory exists."""

    def test_default_examples_when_dir_exists(self, tmp_path):
        md = tmp_path / "rule.md"
        _write_md(md, {
            "name": "srp",
            "displayName": "SRP",
            "category": "solid",
            "description": "desc",
        })
        (tmp_path / "Examples").mkdir()
        (tmp_path / "Examples" / "sample.swift").write_text("// sample")

        result = _run(str(md))
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "examples" in data
        assert len(data["examples"]) == 1
        assert data["examples"][0] == str((tmp_path / "Examples").resolve())

    def test_no_default_examples_when_dir_missing(self, tmp_path):
        md = tmp_path / "rule.md"
        _write_md(md, {
            "name": "srp",
            "displayName": "SRP",
            "category": "solid",
            "description": "desc",
        })
        result = _run(str(md))
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "examples" not in data


class TestExamplesExplicit:
    """Explicit examples in frontmatter — folders and individual files."""

    def test_explicit_folder(self, tmp_path):
        md = tmp_path / "rule.md"
        _write_md(md, {
            "name": "srp",
            "displayName": "SRP",
            "category": "solid",
            "description": "desc",
            "examples": ["MyExamples"],
        })
        result = _run(str(md))
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert len(data["examples"]) == 1
        assert data["examples"][0] == str((tmp_path / "MyExamples").resolve())

    def test_explicit_file(self, tmp_path):
        md = tmp_path / "rule.md"
        _write_md(md, {
            "name": "srp",
            "displayName": "SRP",
            "category": "solid",
            "description": "desc",
            "examples": ["samples/specific-test.swift"],
        })
        result = _run(str(md))
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["examples"][0].endswith("samples/specific-test.swift")

    def test_mixed_folders_and_files(self, tmp_path):
        md = tmp_path / "rule.md"
        _write_md(md, {
            "name": "srp",
            "displayName": "SRP",
            "category": "solid",
            "description": "desc",
            "examples": ["Examples", "extra/edge-case.swift"],
        })
        result = _run(str(md))
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert len(data["examples"]) == 2


class TestInstructionFrontmatter:
    """Test instruction files with PRINCIPLE_FOLDER_ABSOLUTE_PATH token."""

    def test_token_replacement(self, tmp_path):
        review_dir = tmp_path / "SRP" / "review"
        review_dir.mkdir(parents=True)
        md = review_dir / "instructions.md"
        _write_md(md, {
            "name": "srp-review",
            "type": "review",
            "rules": "PRINCIPLE_FOLDER_ABSOLUTE_PATH/rule.md",
            "output_schema": "output.schema.json",
        })
        result = _run(str(md))
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "PRINCIPLE_FOLDER_ABSOLUTE_PATH" not in data["rules"]
        assert data["rules"] == str((tmp_path / "SRP" / "rule.md").resolve())
        assert data["output_schema"] == str((review_dir / "output.schema.json").resolve())


class TestMetadata:
    """_source and _dir metadata fields."""

    def test_source_and_dir(self, tmp_path):
        md = tmp_path / "rule.md"
        _write_md(md, {"name": "test"})
        result = _run(str(md))
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["_source"] == str(md.resolve())
        assert data["_dir"] == str(tmp_path.resolve())


class TestFilesToLoad:
    """files_to_load is a flat list of all files the consumer should read."""

    def test_patterns_and_examples_expanded(self, tmp_path):
        refs_root = tmp_path / "references"
        principle_dir = refs_root / "SRP"
        principle_dir.mkdir(parents=True)
        md = principle_dir / "rule.md"
        _write_md(md, {
            "name": "srp",
            "category": "solid",
            "description": "desc",
            "required_patterns": ["structural/facade"],
        })
        # Create pattern file
        (refs_root / "design_patterns" / "structural").mkdir(parents=True)
        facade = refs_root / "design_patterns" / "structural" / "facade.md"
        facade.write_text("---\nname: facade\n---\n")
        # Create examples dir with files
        (principle_dir / "Examples").mkdir()
        ex1 = principle_dir / "Examples" / "compliant.swift"
        ex2 = principle_dir / "Examples" / "violation.swift"
        ex1.write_text("// compliant")
        ex2.write_text("// violation")

        result = _run(str(md))
        assert result.returncode == 0
        data = json.loads(result.stdout)
        ftl = data["files_to_load"]
        assert str(facade) in ftl
        assert str(ex1) in ftl
        assert str(ex2) in ftl
        assert len(ftl) == 3

    def test_no_files_to_load_when_nothing_to_resolve(self, tmp_path):
        md = tmp_path / "skill.md"
        _write_md(md, {"name": "test", "description": "a skill"})
        result = _run(str(md))
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "files_to_load" not in data

    def test_rules_field_included(self, tmp_path):
        review_dir = tmp_path / "SRP" / "review"
        review_dir.mkdir(parents=True)
        md = review_dir / "instructions.md"
        rule_file = tmp_path / "SRP" / "rule.md"
        rule_file.write_text("---\nname: srp\n---\n")
        _write_md(md, {
            "name": "srp-review",
            "type": "review",
            "rules": "PRINCIPLE_FOLDER_ABSOLUTE_PATH/rule.md",
        })
        result = _run(str(md))
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert str(rule_file.resolve()) in data["files_to_load"]


class TestBooleanAndNumericValues:
    def test_boolean_true(self, tmp_path):
        md = tmp_path / "skill.md"
        _write_md(md, {"name": "test", "user-invocable": True})
        result = _run(str(md))
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["user-invocable"] is True

    def test_boolean_false(self, tmp_path):
        md = tmp_path / "skill.md"
        _write_md(md, {"name": "test", "user-invocable": False})
        result = _run(str(md))
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["user-invocable"] is False

    def test_numeric_value(self, tmp_path):
        md = tmp_path / "agent.md"
        _write_md(md, {"name": "test", "maxTurns": 100})
        result = _run(str(md))
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["maxTurns"] == 100
