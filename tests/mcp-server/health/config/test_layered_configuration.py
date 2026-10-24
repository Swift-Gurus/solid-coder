"""Regression coverage for SPEC-071 user defaults and repository overrides."""

from pathlib import Path
from re import escape

import pytest
from health.config.hc_config_core import find_repository_root
from health.config.solid_coder_config_loader import SolidCoderConfigLoader
from solid_coder_config_error import SolidCoderConfigError


@pytest.fixture
def config_project(tmp_path, monkeypatch):
    home = tmp_path / "home"
    root = tmp_path / "project"
    home.mkdir()
    root.mkdir()
    (root / ".git").mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("SOLID_CODER_TEST_MODEL_PROFILE", raising=False)
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    return home, root


def write_config(path: Path, contents: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")
    return path


@pytest.mark.parametrize("scope", ["user", "repo"])
@pytest.mark.parametrize(
    "preferred,alternate", [(False, False), (True, False), (False, True), (True, True)]
)
def test_alias_selection_uses_only_first_existing_file(
    config_project, scope, preferred, alternate
):
    home, root = config_project
    candidates = (
        (home / ".config/solid-coder/config.toml", home / ".solid-coder/config.toml")
        if scope == "user"
        else (
            root / ".solid-coder/config.toml",
            root / ".config/solid.coder/config.toml",
        )
    )
    if preferred:
        write_config(candidates[0], "[llm]\ntimeout = 11\n")
    if alternate:
        write_config(candidates[1], "[llm]\ntimeout = 22\n")
    config = SolidCoderConfigLoader().load(root)
    assert config.llm.timeout == (11 if preferred else 22 if alternate else 300)


def test_nested_merge_preserves_omitted_keys_false_zero_and_list_replacement(
    config_project,
):
    home, root = config_project
    nested = root / "Sources/Feature"
    nested.mkdir(parents=True)
    write_config(
        home / ".config/solid-coder/config.toml",
        'code_review_on_write_enabled = true\n[llm]\nhost = "http://shared"\ntimeout = 11\ndebug = true\n[frontmatter]\nadditional_categories = ["shared"]\n',
    )
    write_config(
        root / ".solid-coder/config.toml",
        '[llm]\nmodel = "repo-model"\n[frontmatter]\nadditional_categories = ["repo"]\n',
    )
    write_config(root / ".solid-coder/config.local.toml", "[llm]\ntimeout = 22\n")
    write_config(
        nested / ".config/solid.coder/config.toml",
        "code_review_on_write_enabled = false\n[llm]\ntimeout = 33\n",
    )
    write_config(
        nested / ".solid-coder/config.local.toml",
        "[llm]\ntimeout = 0\ndebug = false\n[frontmatter]\nadditional_categories = []\n",
    )
    config = SolidCoderConfigLoader().load(nested)
    assert config.code_review_on_write_enabled is False
    assert config.llm.timeout == 0
    assert config.llm.debug is False
    assert config.llm.host == "http://shared"
    assert config.llm.model == "repo-model"
    assert config.frontmatter.additional_categories == []


@pytest.mark.parametrize("scope", ["user", "repo", "local"])
@pytest.mark.parametrize("failure", ["malformed", "schema", "unreadable"])
def test_selected_invalid_file_reports_source_without_alias_fallback(
    config_project, scope, failure
):
    home, root = config_project
    paths = {
        "user": home / ".config/solid-coder/config.toml",
        "repo": root / ".solid-coder/config.toml",
        "local": root / ".solid-coder/config.local.toml",
    }
    write_config(home / ".solid-coder/config.toml", "[llm]\ntimeout = 22\n")
    write_config(root / ".config/solid.coder/config.toml", "[llm]\ntimeout = 33\n")
    selected = paths[scope]
    if failure == "unreadable":
        selected.mkdir(parents=True)
    else:
        write_config(
            selected,
            "[broken" if failure == "malformed" else '[llm]\ntimeout = "soon"\n',
        )
    with pytest.raises(SolidCoderConfigError, match=escape(str(selected))):
        SolidCoderConfigLoader().load(root)


def test_invalid_lower_layer_is_not_hidden_by_a_valid_override(config_project):
    home, root = config_project
    selected = write_config(
        home / ".config/solid-coder/config.toml", '[llm]\ntimeout = "soon"\n'
    )
    write_config(root / ".solid-coder/config.toml", "[llm]\ntimeout = 10\n")
    with pytest.raises(SolidCoderConfigError, match=escape(str(selected))):
        SolidCoderConfigLoader().load(root)


def test_configuration_is_read_again_on_next_operation(config_project):
    home, root = config_project
    selected = write_config(
        home / ".config/solid-coder/config.toml", "[llm]\ntimeout = 11\n"
    )
    loader = SolidCoderConfigLoader()
    assert loader.load(root).llm.timeout == 11
    selected.write_text("[llm]\ntimeout = 22\n", encoding="utf-8")
    assert loader.load(root).llm.timeout == 22


def test_nested_repository_stops_project_config_inheritance(config_project):
    _, root = config_project
    write_config(root / ".solid-coder/config.toml", "[llm]\ntimeout = 11\n")
    nested = root / "nested"
    nested.mkdir()
    (nested / ".git").write_text("gitdir: ../worktrees/nested\n", encoding="utf-8")
    leaf = nested / "Sources"
    leaf.mkdir()
    write_config(nested / ".solid-coder/config.toml", "[llm]\ntimeout = 22\n")
    assert find_repository_root(leaf) == nested.resolve()
    assert SolidCoderConfigLoader().load(leaf).llm.timeout == 22


def test_explicit_directory_precedes_environment_and_process_directory(
    config_project, monkeypatch
):
    _, root = config_project
    other = root / "other"
    other.mkdir()
    (other / ".git").mkdir()
    write_config(root / ".solid-coder/config.toml", "[llm]\ntimeout = 11\n")
    write_config(other / ".solid-coder/config.toml", "[llm]\ntimeout = 22\n")
    monkeypatch.chdir(other)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(root))
    loader = SolidCoderConfigLoader()
    assert loader.load().llm.timeout == 11
    assert loader.load(other).llm.timeout == 22
    monkeypatch.delenv("CLAUDE_PROJECT_DIR")
    assert loader.load().llm.timeout == 22
