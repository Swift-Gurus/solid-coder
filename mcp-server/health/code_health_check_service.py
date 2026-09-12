"""Coordinates one prospective code-health validation request."""

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
        checker_factory: Callable[..., HealthChecking],
        mcp_config: str,
    ) -> None:
        self._strategy_selector = strategy_selector
        self._checker_factory = checker_factory
        self._mcp_config = mcp_config

    def check(self, request: CodeHealthCheckRequest) -> Optional[list]:
        strategy = self._strategy_selector()
        strategy.apply_env()
        checker = self._checker_factory(
            mcp_config=self._mcp_config,
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
