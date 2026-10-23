"""Resolves isolated output storage for legacy health reviews."""

from health.gateway.gateway_command_runner import GatewayInvoking
from output_path_resolver import OutputPathResolving

"""
solid-name: HealthOutputPathResolver
solid-category: service
solid-description: Provides an isolated output directory for one health-check invocation.
"""


class HealthOutputPathResolver:
    def __init__(self, invoker: GatewayInvoking, fallback: OutputPathResolving) -> None:
        self._invoker = invoker
        self._fallback = fallback

    def resolve(self, session_id: str) -> str:
        result = self._invoker.invoke(
            "get_output_path",
            extra_args=["--operation", "health"],
            result_key="output_root",
        )
        return result if result else self._fallback.resolve(session_id)
