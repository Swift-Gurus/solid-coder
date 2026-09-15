"""Checks the public health-check selector through actual TOML loading."""

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_ROOT / "mcp-server" / "health" / "config"))

from hc_config_schema import load_config
from solid_coder_config_error import SolidCoderConfigError


"""
solid-name: TestHealthCheckModeConfiguration
solid-category: unit-test
solid-spec: [SPEC-050]
solid-description: Verifies typed health-check selection, project overrides, and configuration reloads.
"""
class TestHealthCheckModeConfiguration:
    def test_omitted_mode_defaults_to_workflow(self, tmp_path):
        assert load_config(tmp_path).feature_flags.health_check_mode.value == "workflow"

    @pytest.mark.parametrize("mode", ["legacy", "workflow"])
    def test_loads_explicit_mode(self, tmp_path, mode):
        config_dir = tmp_path / ".solid-coder"
        config_dir.mkdir()
        (config_dir / "config.toml").write_text(
            f'[feature_flags]\nhealth_check_mode = "{mode}"\n',
        )
        assert load_config(tmp_path).feature_flags.health_check_mode.value == mode

    @pytest.mark.parametrize("value", ['"automatic"', '"Legacy"', "true", "42"])
    def test_invalid_mode_is_a_field_specific_error(self, tmp_path, value):
        config_dir = tmp_path / ".solid-coder"
        config_dir.mkdir()
        (config_dir / "config.toml").write_text(
            f"[feature_flags]\nhealth_check_mode = {value}\n",
        )
        with pytest.raises(SolidCoderConfigError, match="feature_flags.health_check_mode"):
            load_config(tmp_path)

    def test_local_override_preserves_other_flags_and_reloads(self, tmp_path):
        config_dir = tmp_path / ".solid-coder"
        config_dir.mkdir()
        (config_dir / "config.toml").write_text(
            '[feature_flags]\nhealth_check_mode = "workflow"\n'
            "flow_plain_text_response = false\n",
        )
        local = config_dir / "config.local.toml"
        local.write_text('[feature_flags]\nhealth_check_mode = "legacy"\n')
        config = load_config(tmp_path)
        assert config.feature_flags.health_check_mode.value == "legacy"
        assert config.feature_flags.flow_plain_text_response is False
        local.write_text('[feature_flags]\nhealth_check_mode = "workflow"\n')
        assert load_config(tmp_path).feature_flags.health_check_mode.value == "workflow"
