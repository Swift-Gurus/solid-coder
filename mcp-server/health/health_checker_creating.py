"""Defines construction of a checker for one prospective review request."""

from typing import Protocol

from code_health_check_request import CodeHealthCheckRequest
from hc_checker import HealthChecking


"""
solid-name: HealthCheckerCreating
solid-category: abstraction
solid-spec: [SPEC-049, SPEC-050]
solid-description: Contract for creating request-scoped source-health checkers.
"""
class HealthCheckerCreating(Protocol):
    def make(self, request: CodeHealthCheckRequest) -> HealthChecking: ...
