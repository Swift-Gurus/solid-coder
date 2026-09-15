"""Coordinates one prospective code-health validation request."""

from code_health_check_request import CodeHealthCheckRequest
from health_checker_creating import HealthCheckerCreating


"""
solid-name: CodeHealthCheckService
solid-category: service
solid-description: Coordinates configured health validation for prospective source requests.
solid-tags: [hook]
"""
class CodeHealthCheckService:
    def __init__(
        self,
        checker_factory: HealthCheckerCreating,
    ) -> None:
        self._checker_factory = checker_factory

    def check(self, request: CodeHealthCheckRequest) -> list:
        checker = self._checker_factory.make(request)
        violations = checker.check(
            request.content,
            request.path,
            request.language,
            request.parent_session_id,
            patch_context=request.patch_context,
            principle_names=request.principle_names,
        )
        if violations is None:
            raise RuntimeError("Health checker returned no result")
        return violations
