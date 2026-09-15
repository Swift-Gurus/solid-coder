"""Verifies configured health-check selection through the active write gate."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from _path_bootstrap import ensure_on_path

ensure_on_path(
    Path(__file__).resolve().parents[3] / "mcp-server" / "hooks",
    Path(__file__).resolve().parent,
)

from write_gate_coordinator_factory import WriteGateCoordinatorFactory  # noqa: E402


"""
solid-name: TestHealthCheckModeGateIntegration
solid-category: integration-test
solid-spec: [SPEC-050]
solid-description: Verifies the write gate routes prospective content through the checker selected by project TOML.
"""
class TestHealthCheckModeGateIntegration:
    @pytest.mark.parametrize("mode", ["legacy", "workflow"])
    def test_routes_unwritten_source_through_selected_checker(
        self,
        tmp_path: Path,
        mode: str,
    ) -> None:
        config_directory = tmp_path / ".solid-coder"
        config_directory.mkdir()
        (config_directory / "config.toml").write_text(
            f'[feature_flags]\nhealth_check_mode = "{mode}"\n',
            encoding="utf-8",
        )
        destination = tmp_path / "ProspectiveView.swift"
        content = "struct ProspectiveView {\n" + "    let value = 1\n" * 40 + "}\n"
        gate = MagicMock()

        with patch(
            "configured_health_checker_factory.LegacyHealthCheckerFactory"
        ) as legacy, patch(
            "configured_health_checker_factory.WorkflowHealthCheckerFactory"
        ) as workflow, patch("configured_health_checker_factory.GateLogger"):
            selected = legacy if mode == "legacy" else workflow
            other = workflow if mode == "legacy" else legacy
            selected.return_value.make.return_value.check.return_value = []

            WriteGateCoordinatorFactory().make_coordinator(gate).run(
                tool_name="Write",
                tool_input={"file_path": str(destination), "content": content},
                file_path=str(destination),
                language="Swift",
                session_id="parent-session",
                cwd=str(tmp_path),
            )

        other.assert_not_called()
        request = selected.return_value.make.call_args.args[0]
        assert request.content == content
        assert request.path == str(destination)
        assert request.parent_session_id == "parent-session"
        assert request.cwd == str(tmp_path)
        assert not destination.exists()
        gate.allow.assert_called_once_with()
        gate.block.assert_not_called()
