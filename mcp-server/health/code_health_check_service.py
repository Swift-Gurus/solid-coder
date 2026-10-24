"""Coordinates one prospective code-health validation request."""

from collections.abc import Callable
from pathlib import Path

from code_health_check_request import CodeHealthCheckRequest
from health_check_outcome import HealthCheckOutcome
from health_checker_creating import HealthCheckerCreating
from source.repository_target_resolver import RepositoryTargetResolving

"""
solid-name: CodeHealthCheckService
solid-category: service
solid-spec: [SPEC-071]
solid-description: Coordinates configured health validation for prospective source requests.
solid-tags: [hook]
"""


class CodeHealthCheckService:
    def __init__(
        self,
        checker_factory: HealthCheckerCreating[HealthCheckOutcome],
        targets: RepositoryTargetResolving,
        current_directory: Callable[[], Path],
    ) -> None:
        self._checker_factory = checker_factory
        self._targets = targets
        self._current_directory = current_directory

    def check(self, request: CodeHealthCheckRequest) -> HealthCheckOutcome:
        cwd = Path(request.cwd) if request.cwd else self._current_directory()
        path = self._targets.resolve(cwd, Path(request.path))
        request = request.model_copy(update={"path": str(path), "cwd": str(cwd)})
        checker = self._checker_factory.make(request)
        outcome = checker.check(
            request.content,
            request.path,
            request.language,
            request.parent_session_id,
            patch_context=request.patch_context,
            principle_names=request.principle_names,
        )
        if outcome is None:
            raise RuntimeError("Health checker returned no result")
        return outcome
