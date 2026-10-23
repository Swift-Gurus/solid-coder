"""Invokes legacy fix guidance and fix submission through the gateway."""

from typing import Protocol

from health.gateway.gateway_command_runner import GatewayInvoking
from json_serializer import JsonSerializer, JsonSerializing

"""
solid-name: FixInvoking
solid-category: abstraction
solid-description: Contract for loading violation fixes and submitting completed fixes.
"""


class FixInvoking(Protocol):
    def load_fix(self, metric_ids: list) -> str: ...
    def submit_fix(self, output_dir: str, fixes: list) -> str: ...


_DEFAULT_SERIALIZER: JsonSerializing = JsonSerializer()


"""
solid-name: GatewayFixInvoker
solid-category: service
solid-description: Provides legacy fix guidance and records fix submissions through gateway operations.
"""


class GatewayFixInvoker:
    def __init__(
        self,
        invoker: GatewayInvoking,
        serializer: JsonSerializing = _DEFAULT_SERIALIZER,
    ) -> None:
        self._invoker = invoker
        self._serializer = serializer

    def load_fix(self, metric_ids: list) -> str:
        result = self._invoker.invoke(
            "load_fix_for_violation",
            extra_args=["--metric_ids"] + [str(metric) for metric in metric_ids],
            result_key="content",
            default="",
        )
        return result or ""

    def submit_fix(self, output_dir: str, fixes: list) -> str:
        result = self._invoker.invoke(
            "submit_fix",
            extra_args=[
                "--output_dir",
                output_dir,
                "--fixes",
                self._serializer.serialize(fixes),
            ],
            result_key=None,
            default="{}",
        )
        return result or "{}"
