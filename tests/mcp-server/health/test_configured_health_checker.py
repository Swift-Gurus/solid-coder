"""Verifies checker selection through the common prospective-review service."""

import json
import sys
from hashlib import sha256
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_ROOT = Path(__file__).resolve().parents[3]
for _part in ("", "health", "health/config", "health/llm", "health/codex", "gate", "output", "patch", "utils", "session"):
    sys.path.insert(0, str(_ROOT / "mcp-server" / _part))

from code_health_check_request import CodeHealthCheckRequest
from code_health_check_service import CodeHealthCheckService
from health.configured_health_checker_factory import ConfiguredHealthCheckerFactory


"""
solid-name: TestConfiguredHealthChecker
solid-category: unit-test
solid-spec: [SPEC-050]
solid-description: Verifies one configured construction point selects matching checker capabilities and preserves prospective input.
"""
class TestConfiguredHealthChecker:
    @pytest.mark.parametrize("mode", ["legacy", "workflow"])
    def test_selects_matching_checker_and_tools(self, tmp_path, mode):
        config_dir = tmp_path / ".solid-coder"
        config_dir.mkdir()
        (config_dir / "config.toml").write_text(
            f'[feature_flags]\nhealth_check_mode = "{mode}"\n'
            '[llm]\nbackend = "codex"\nmodel = "gpt-5.6-terra"\ntimeout = 123\n',
        )
        request = CodeHealthCheckRequest(
            content="final class Prospective {}",
            path=str(tmp_path / "New.swift"),
            language="Swift",
            parent_session_id="parent-123",
            cwd=str(tmp_path),
        )
        with patch("health.configured_health_checker_factory.LegacyHealthCheckerFactory") as legacy, \
             patch("health.configured_health_checker_factory.WorkflowHealthCheckerFactory") as workflow, \
             patch("health.configured_health_checker_factory.GateLogger") as gate_logger:
            selected = legacy if mode == "legacy" else workflow
            other = workflow if mode == "legacy" else legacy
            selected.return_value.make.return_value.check.return_value = []
            service = CodeHealthCheckService(
                checker_factory=ConfiguredHealthCheckerFactory(plugin_root=_ROOT),
            )
            assert service.check(request) == []
            other.assert_not_called()
            construction = selected.call_args.kwargs
            assert construction["config"].llm.model == "gpt-5.6-terra"
            assert construction["config"].llm.timeout == 123
            servers = json.loads(construction["mcp_config"])["mcpServers"]
            assert set(servers) == ({"docs", "pipeline"} if mode == "legacy" else {"solid-coder-flow-engine"})
            selected.return_value.make.assert_called_once_with(request)
            selected.return_value.make.return_value.check.assert_called_once_with(
                request.content, request.path, "Swift", "parent-123",
                patch_context=None, principle_names=[],
            )
            audit = gate_logger.return_value.log.call_args.args[0]
            assert f"health_check_mode={mode}" in audit
            assert "backend=codex model=gpt-5.6-terra" in audit
            assert f"target={request.path}" in audit
            assert (
                f"source_sha256={sha256(request.content.encode('utf-8')).hexdigest()}"
                in audit
            )
            assert not Path(request.path).exists()

    def test_checker_failure_is_not_a_successful_empty_review(self):
        checker_factory = MagicMock()
        checker_factory.make.return_value.check.return_value = None
        service = CodeHealthCheckService(checker_factory=checker_factory)
        with pytest.raises(RuntimeError, match="no result"):
            service.check(CodeHealthCheckRequest(
                content="class Example {}", path="/project/Example.swift",
                language="Swift", parent_session_id="parent",
            ))

    def test_selected_checker_error_does_not_retry(self):
        checker_factory = MagicMock()
        checker = checker_factory.make.return_value
        checker.check.side_effect = TimeoutError("review timed out")
        service = CodeHealthCheckService(checker_factory=checker_factory)
        with pytest.raises(TimeoutError, match="review timed out"):
            service.check(CodeHealthCheckRequest(
                content="class Example {}", path="/project/Example.swift",
                language="Swift", parent_session_id="parent",
            ))
        assert checker_factory.make.call_count == 1
        assert checker.check.call_count == 1
