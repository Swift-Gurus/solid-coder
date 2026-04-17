#!/usr/bin/env python3
"""Tests for discover-principles.py."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

SCRIPT = str(
    Path(__file__).resolve().parent.parent / "discover-principles.py"
)


def _run(*args: str) -> tuple:
    """Run discover-principles.py with args, return (returncode, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, SCRIPT, *args],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def _make_rule(tmp: Path, name: str, frontmatter: str) -> Path:
    """Create a principle folder with rule.md."""
    folder = tmp / name
    folder.mkdir(parents=True, exist_ok=True)
    rule = folder / "rule.md"
    rule.write_text(f"---\n{frontmatter}\n---\n\n# {name}\n")
    return rule


class TestDiscovery:
    """Test principle discovery without filtering."""

    def test_discovers_all_principles(self, tmp_path):
        _make_rule(tmp_path, "SRP", "name: srp\ndisplayName: Single Responsibility")
        _make_rule(tmp_path, "OCP", "name: ocp\ndisplayName: Open/Closed")

        rc, out, _ = _run("--refs-root", str(tmp_path))
        assert rc == 0
        data = json.loads(out)
        names = [p["name"] for p in data["active_principles"]]
        assert "ocp" in names
        assert "srp" in names
        assert data["skipped_principles"] == []
        assert data["all_candidate_tags"] == []

    def test_discovers_with_tags(self, tmp_path):
        _make_rule(tmp_path, "SRP", "name: srp")
        _make_rule(tmp_path, "SwiftUI", "name: swiftui-views\ntags:\n  - swiftui\n  - ui")

        rc, out, _ = _run("--refs-root", str(tmp_path))
        assert rc == 0
        data = json.loads(out)
        # Discovery mode: all active (no filtering)
        assert len(data["active_principles"]) == 2
        assert sorted(data["all_candidate_tags"]) == ["swiftui", "ui"]

    def test_no_principles_found(self, tmp_path):
        rc, out, _ = _run("--refs-root", str(tmp_path))
        assert rc == 0
        data = json.loads(out)
        assert data["active_principles"] == []

    def test_skips_no_frontmatter(self, tmp_path):
        folder = tmp_path / "BAD"
        folder.mkdir()
        (folder / "rule.md").write_text("# No frontmatter\n")

        _make_rule(tmp_path, "SRP", "name: srp")

        rc, out, _ = _run("--refs-root", str(tmp_path))
        assert rc == 0
        data = json.loads(out)
        assert len(data["active_principles"]) == 1

    def test_custom_glob(self, tmp_path):
        # Nested structure
        nested = tmp_path / "core" / "SRP"
        nested.mkdir(parents=True)
        (nested / "rule.md").write_text("---\nname: srp\n---\n# SRP\n")

        rc, out, _ = _run("--refs-root", str(tmp_path), "--glob", "core/*/rule.md")
        assert rc == 0
        data = json.loads(out)
        assert len(data["active_principles"]) == 1
        assert data["active_principles"][0]["name"] == "srp"


class TestFiltering:
    """Test principle filtering with --matched-tags."""

    def test_no_tags_always_active(self, tmp_path):
        _make_rule(tmp_path, "SRP", "name: srp")

        rc, out, _ = _run("--refs-root", str(tmp_path), "--matched-tags", "swiftui")
        assert rc == 0
        data = json.loads(out)
        assert len(data["active_principles"]) == 1
        assert data["active_principles"][0]["name"] == "srp"

    def test_matching_tag_activates(self, tmp_path):
        _make_rule(tmp_path, "SRP", "name: srp")
        _make_rule(tmp_path, "SwiftUI", "name: swiftui-views\ntags:\n  - swiftui\n  - ui")

        rc, out, _ = _run("--refs-root", str(tmp_path), "--matched-tags", "swiftui")
        assert rc == 0
        data = json.loads(out)
        assert len(data["active_principles"]) == 2
        assert data["skipped_principles"] == []

    def test_no_matching_tag_skips(self, tmp_path):
        _make_rule(tmp_path, "SRP", "name: srp")
        _make_rule(tmp_path, "SwiftUI", "name: swiftui-views\ntags:\n  - swiftui\n  - ui")

        rc, out, _ = _run("--refs-root", str(tmp_path), "--matched-tags", "combine")
        assert rc == 0
        data = json.loads(out)
        active_names = [p["name"] for p in data["active_principles"]]
        assert "srp" in active_names
        assert "swiftui-views" not in active_names
        assert len(data["skipped_principles"]) == 1
        assert data["skipped_principles"][0]["reason"] == "no matching tags"

    def test_case_insensitive_matching(self, tmp_path):
        _make_rule(tmp_path, "SwiftUI", "name: swiftui-views\ntags:\n  - SwiftUI")

        rc, out, _ = _run("--refs-root", str(tmp_path), "--matched-tags", "swiftui")
        assert rc == 0
        data = json.loads(out)
        assert len(data["active_principles"]) == 1

    def test_multiple_matched_tags(self, tmp_path):
        _make_rule(tmp_path, "SwiftUI", "name: swiftui-views\ntags:\n  - swiftui")
        _make_rule(tmp_path, "TCA", "name: tca\ntags:\n  - tca")
        _make_rule(tmp_path, "SRP", "name: srp")

        rc, out, _ = _run("--refs-root", str(tmp_path), "--matched-tags", "swiftui,tca")
        assert rc == 0
        data = json.loads(out)
        assert len(data["active_principles"]) == 3
        assert data["skipped_principles"] == []

    def test_partial_match_activates(self, tmp_path):
        _make_rule(tmp_path, "SwiftUI", "name: swiftui-views\ntags:\n  - swiftui\n  - ui")

        # Only one of the two tags matches
        rc, out, _ = _run("--refs-root", str(tmp_path), "--matched-tags", "ui")
        assert rc == 0
        data = json.loads(out)
        assert len(data["active_principles"]) == 1

    def test_single_string_tag(self, tmp_path):
        _make_rule(tmp_path, "SwiftUI", "name: swiftui-views\ntags: swiftui")

        rc, out, _ = _run("--refs-root", str(tmp_path), "--matched-tags", "swiftui")
        assert rc == 0
        data = json.loads(out)
        assert len(data["active_principles"]) == 1


class TestOutput:
    """Test output structure."""

    def test_output_includes_folder_and_rule_path(self, tmp_path):
        _make_rule(tmp_path, "SRP", "name: srp\ndisplayName: Single Responsibility")

        rc, out, _ = _run("--refs-root", str(tmp_path))
        assert rc == 0
        data = json.loads(out)
        p = data["active_principles"][0]
        assert p["folder"].endswith("/SRP")
        assert p["rule_path"].endswith("/SRP/rule.md")
        assert p["displayName"] == "Single Responsibility"
        assert p["tags"] is None

    def test_candidate_tags_collected_from_all(self, tmp_path):
        _make_rule(tmp_path, "A", "name: a\ntags:\n  - swiftui\n  - ui")
        _make_rule(tmp_path, "B", "name: b\ntags:\n  - tca\n  - ui")
        _make_rule(tmp_path, "C", "name: c")

        rc, out, _ = _run("--refs-root", str(tmp_path))
        assert rc == 0
        data = json.loads(out)
        assert sorted(data["all_candidate_tags"]) == ["swiftui", "tca", "ui"]


class TestReviewInput:
    """Test --review-input flag."""

    def test_reads_matched_tags_from_json(self, tmp_path):
        _make_rule(tmp_path, "SRP", "name: srp")
        _make_rule(tmp_path, "SwiftUI", "name: swiftui-views\ntags:\n  - swiftui")

        ri = tmp_path / "review-input.json"
        ri.write_text(json.dumps({"matched_tags": ["swiftui"]}))

        rc, out, _ = _run("--refs-root", str(tmp_path), "--review-input", str(ri))
        assert rc == 0
        data = json.loads(out)
        assert len(data["active_principles"]) == 2  # srp (no tags) + swiftui (matched)

    def test_empty_matched_tags_skips_tagged_principles(self, tmp_path):
        _make_rule(tmp_path, "SRP", "name: srp")
        _make_rule(tmp_path, "SwiftUI", "name: swiftui-views\ntags:\n  - swiftui")

        ri = tmp_path / "review-input.json"
        ri.write_text(json.dumps({"matched_tags": []}))

        rc, out, _ = _run("--refs-root", str(tmp_path), "--review-input", str(ri))
        assert rc == 0
        data = json.loads(out)
        # Empty matched_tags = filter mode with no matches; tagged principles skipped
        active_names = [p["name"] for p in data["active_principles"]]
        assert "srp" in active_names
        assert "swiftui-views" not in active_names
        assert len(data["active_principles"]) == 1
        assert len(data["skipped_principles"]) == 1
        assert data["skipped_principles"][0]["reason"] == "no matching tags"

    def test_skips_with_no_match(self, tmp_path):
        _make_rule(tmp_path, "SwiftUI", "name: swiftui-views\ntags:\n  - swiftui")

        ri = tmp_path / "review-input.json"
        ri.write_text(json.dumps({"matched_tags": ["combine"]}))

        rc, out, _ = _run("--refs-root", str(tmp_path), "--review-input", str(ri))
        assert rc == 0
        data = json.loads(out)
        assert len(data["active_principles"]) == 0
        assert len(data["skipped_principles"]) == 1

    def test_missing_review_input_file(self, tmp_path):
        rc, _, err = _run("--refs-root", str(tmp_path), "--review-input", "/nonexistent.json")
        assert rc == 1
        assert "not found" in err

    def test_review_input_without_matched_tags_key(self, tmp_path):
        _make_rule(tmp_path, "SRP", "name: srp")

        ri = tmp_path / "review-input.json"
        ri.write_text(json.dumps({"source_type": "changes"}))

        rc, out, _ = _run("--refs-root", str(tmp_path), "--review-input", str(ri))
        assert rc == 0
        data = json.loads(out)
        # No matched_tags key = discovery mode
        assert len(data["active_principles"]) == 1


class TestProfileFilter:
    """Test --profile filter — principles declare which profiles they support via `profile:` frontmatter."""

    def test_no_profile_field_means_available_everywhere(self, tmp_path):
        _make_rule(tmp_path, "SRP", "name: srp")
        for profile in ("review", "code"):
            rc, out, _ = _run("--refs-root", str(tmp_path), "--profile", profile)
            assert rc == 0, f"profile={profile}"
            data = json.loads(out)
            assert len(data["active_principles"]) == 1
            assert data["skipped_principles"] == []

    def test_profile_list_excludes_other_profiles(self, tmp_path):
        _make_rule(tmp_path, "CodeSmells", "name: code-smells\nprofile:\n  - code")

        rc, out, _ = _run("--refs-root", str(tmp_path), "--profile", "review")
        data = json.loads(out)
        assert len(data["active_principles"]) == 0
        assert len(data["skipped_principles"]) == 1
        assert "profile 'review'" in data["skipped_principles"][0]["reason"]

        rc, out, _ = _run("--refs-root", str(tmp_path), "--profile", "code")
        data = json.loads(out)
        assert [p["name"] for p in data["active_principles"]] == ["code-smells"]

    def test_inline_profile_list(self, tmp_path):
        _make_rule(tmp_path, "X", "name: x\nprofile: [code, review]")

        for profile in ("review", "code"):
            rc, out, _ = _run("--refs-root", str(tmp_path), "--profile", profile)
            data = json.loads(out)
            assert [p["name"] for p in data["active_principles"]] == ["x"]

    def test_no_profile_arg_ignores_profile_field(self, tmp_path):
        _make_rule(tmp_path, "CodeOnly", "name: co\nprofile:\n  - code")
        _make_rule(tmp_path, "Normal", "name: normal")

        rc, out, _ = _run("--refs-root", str(tmp_path))
        data = json.loads(out)
        names = sorted(p["name"] for p in data["active_principles"])
        assert names == ["co", "normal"]

    def test_profile_combines_with_tag_filter(self, tmp_path):
        _make_rule(tmp_path, "Tagged", "name: tagged\ntags: [swiftui]\nprofile: [review]")
        _make_rule(tmp_path, "Other", "name: other\ntags: [swiftui]\nprofile: [code]")

        rc, out, _ = _run(
            "--refs-root", str(tmp_path),
            "--matched-tags", "swiftui",
            "--profile", "review",
        )
        data = json.loads(out)
        assert [p["name"] for p in data["active_principles"]] == ["tagged"]
        assert any(s["name"] == "other" for s in data["skipped_principles"])


class TestErrors:
    """Test error cases."""

    def test_invalid_refs_root(self):
        rc, _, err = _run("--refs-root", "/nonexistent/path")
        assert rc == 1
        assert "not a directory" in err

    def test_missing_refs_root_arg(self):
        rc, _, _ = _run()
        assert rc != 0
