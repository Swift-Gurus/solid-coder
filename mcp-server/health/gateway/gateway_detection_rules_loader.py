"""Loads matched legacy detection rules through the gateway."""

from typing import Protocol

from health.gateway.gateway_command_runner import GatewayInvoking

"""
solid-name: MatchedDetectionRulesLoading
solid-category: abstraction
solid-description: Contract for loading detection rules selected by matched tags.
"""


class MatchedDetectionRulesLoading(Protocol):
    def load_detection_rules(self, matched_tags: list) -> dict | None: ...


"""
solid-name: GatewayDetectionRulesLoader
solid-category: service
solid-description: Loads the legacy detection-rule payload for matched discovery tags.
"""


class GatewayDetectionRulesLoader:
    def __init__(self, invoker: GatewayInvoking) -> None:
        self._invoker = invoker

    def load_detection_rules(self, matched_tags: list) -> dict | None:
        return self._invoker.invoke(
            "load_detection_rules",
            extra_args=["--matched_tags", ",".join(matched_tags)],
        )
