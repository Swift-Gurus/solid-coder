"""Checks the public health-check selector through actual TOML loading."""

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_ROOT / "mcp-server" / "health" / "config"))

from solid_coder_config_loader import SolidCoderConfigLoader
from solid_coder_config_error import SolidCoderConfigError


"""
solid-name: TestHealthCheckModeConfiguration
solid-category: unit-test
solid-spec: [SPEC-050]
solid-description: Verifies typed health-check selection, project overrides, and configuration reloads.
"""
class TestHealthCheckModeConfiguration:
    def test_omitted_mode_defaults_to_workflow(self, tmp_path):
        assert SolidCoderConfigLoader().load(tmp_path).feature_flags.health_check_mode.value == "workflow"

    @pytest.mark.parametrize("mode", ["legacy", "workflow"])
    @pytest.mark.parametrize("relative_directory", [".", "ios/Tools/BuildInsights"])
    def test_loads_explicit_mode(self, tmp_path, mode, relative_directory):
        (tmp_path / ".git").mkdir()
        config_dir = tmp_path / ".solid-coder"
        config_dir.mkdir()
        (config_dir / "config.toml").write_text(
            f'[feature_flags]\nhealth_check_mode = "{mode}"\n',
        )
        working_directory = tmp_path / relative_directory
        working_directory.mkdir(parents=True, exist_ok=True)

        assert SolidCoderConfigLoader().load(working_directory).feature_flags.health_check_mode.value == mode

    @pytest.mark.parametrize("value", ['"automatic"', '"Legacy"', "true", "42"])
    @pytest.mark.parametrize("relative_directory", [".", "ios/Tools/BuildInsights"])
    def test_invalid_mode_is_a_field_specific_error(self, tmp_path, value, relative_directory):
        config_dir = tmp_path / ".solid-coder"
        config_dir.mkdir()
        (config_dir / "config.toml").write_text(
            f"[feature_flags]\nhealth_check_mode = {value}\n",
        )
        working_directory = tmp_path / relative_directory
        working_directory.mkdir(parents=True, exist_ok=True)
        with pytest.raises(SolidCoderConfigError, match="feature_flags.health_check_mode"):
            SolidCoderConfigLoader().load(working_directory)

    @pytest.mark.parametrize("relative_directory", [".", "ios/Tools/BuildInsights"])
    def test_local_override_preserves_other_flags_and_reloads(self, tmp_path, relative_directory):
        config_dir = tmp_path / ".solid-coder"
        config_dir.mkdir()
        (config_dir / "config.toml").write_text(
            '[feature_flags]\nhealth_check_mode = "workflow"\n'
            "flow_plain_text_response = false\n",
        )
        local = config_dir / "config.local.toml"
        local.write_text('[feature_flags]\nhealth_check_mode = "legacy"\n')
        working_directory = tmp_path / relative_directory
        working_directory.mkdir(parents=True, exist_ok=True)
        config = SolidCoderConfigLoader().load(working_directory)
        assert config.feature_flags.health_check_mode.value == "legacy"
        assert config.feature_flags.flow_plain_text_response is False
        local.write_text('[feature_flags]\nhealth_check_mode = "workflow"\n')
        assert SolidCoderConfigLoader().load(working_directory).feature_flags.health_check_mode.value == "workflow"

    def test_child_llm_override_preserves_parent_health_mode_and_backend(self, tmp_path):
        config_dir = tmp_path / ".solid-coder"
        config_dir.mkdir()
        (config_dir / "config.toml").write_text(
            'code_review_on_write_enabled = true\n'
            '[feature_flags]\nhealth_check_mode = "legacy"\n'
            '[llm]\nbackend = "codex"\ntimeout = 1000\n',
        )
        working_directory = tmp_path / "ios" / "Tools" / "BuildInsights"
        child_config_dir = working_directory / ".solid-coder"
        child_config_dir.mkdir(parents=True)
        (child_config_dir / "config.toml").write_text('[llm]\ntimeout = 120\n')

        config = SolidCoderConfigLoader().load(working_directory)

        assert config.feature_flags.health_check_mode.value == "legacy"
        assert config.llm.backend == "codex"
        assert config.llm.timeout == 120
        assert config.code_review_on_write_enabled is True

    @pytest.mark.parametrize("filename", ["config.toml", "config.local.toml"])
    @pytest.mark.parametrize("parent_mode,child_mode", [("legacy", "workflow"), ("workflow", "legacy")])
    def test_nearer_mode_overrides_parent_local_setting(self, tmp_path, filename, parent_mode, child_mode):
        config_dir = tmp_path / ".solid-coder"
        config_dir.mkdir()
        (config_dir / "config.local.toml").write_text(
            f'[feature_flags]\nhealth_check_mode = "{parent_mode}"\n',
        )
        child = tmp_path / "ios"
        child_config_dir = child / ".solid-coder"
        child_config_dir.mkdir(parents=True)
        (child_config_dir / filename).write_text(
            f'[feature_flags]\nhealth_check_mode = "{child_mode}"\n',
        )
        working_directory = child / "Tools" / "BuildInsights"
        working_directory.mkdir(parents=True)

        config = SolidCoderConfigLoader().load(working_directory)

        assert config.feature_flags.health_check_mode.value == child_mode

    @pytest.mark.parametrize("create_git_marker", [Path.mkdir, Path.touch])
    def test_does_not_inherit_config_outside_git_root(self, tmp_path, create_git_marker):
        config_dir = tmp_path / ".solid-coder"
        config_dir.mkdir()
        (config_dir / "config.toml").write_text(
            '[feature_flags]\nhealth_check_mode = "legacy"\n',
        )
        repository = tmp_path / "independent-repository"
        repository.mkdir()
        create_git_marker(repository / ".git")
        working_directory = repository / "Sources"
        working_directory.mkdir()

        config = SolidCoderConfigLoader().load(working_directory)

        assert config.feature_flags.health_check_mode.value == "workflow"
