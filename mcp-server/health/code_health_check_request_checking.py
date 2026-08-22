"""Defines prospective code-health request checking."""

from typing import Optional, Protocol

from code_health_check_request import CodeHealthCheckRequest


"""
solid-name: CodeHealthCheckRequestChecking
solid-category: abstraction
solid-description: Contract for validating one typed prospective source-health request.
solid-tags: [hook]
"""
class CodeHealthCheckRequestChecking(Protocol):
    def check(self, request: CodeHealthCheckRequest) -> Optional[list]: ...
