"""Coordinates one prospective code-health validation request."""

from pathlib import Path
from typing import Callable, Optional

from code_health_check_request import CodeHealthCheckRequest
from hc_checker import HealthChecking
from runner_strategy_base import RunnerStrategyBase


"""
solid-name: CodeHealthCheckService
solid-category: service
solid-description: Coordinates configured health validation for prospective source requests.
solid-tags: [hook]
"""
class CodeHealthCheckService:
    def __init__(
        self,
        strategy_selector: Callable[[], RunnerStrategyBase],
        mcp_config_builder: Callable[[Path], str],
        checker_factory: Callable[..., HealthChecking],
        plugin_root: Path,
    ) -> None:
        self._strategy_selector = strategy_selector
        self._mcp_config_builder = mcp_config_builder
        self._checker_factory = checker_factory
        self._plugin_root = plugin_root

    def check(self, request: CodeHealthCheckRequest) -> Optional[list]:
        strategy = self._strategy_selector()
        strategy.apply_env()
        checker = self._checker_factory(
            mcp_config=self._mcp_config_builder(self._plugin_root),
            session_id=request.parent_session_id,
            file_path=request.path,
            cwd=request.cwd,
        )
        return checker.check(
            request.content,
            request.path,
            request.language,
            request.parent_session_id,
            patch_context=request.patch_context,
            principle_names=request.principle_names,
        )
