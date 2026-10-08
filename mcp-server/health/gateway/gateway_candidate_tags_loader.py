"""Loads legacy health-check rule discovery tags."""

from typing import Protocol

from health.gateway.gateway_command_runner import GatewayInvoking


"""
solid-name: CandidateTagsLoading
solid-category: abstraction
solid-description: Contract for loading the available rule-discovery tags.
"""
class CandidateTagsLoading(Protocol):
    def get_candidate_tags(self) -> list: ...


"""
solid-name: GatewayCandidateTagsLoader
solid-category: service
solid-description: Loads available rule-discovery tags for health-check activation.
"""
class GatewayCandidateTagsLoader:
    def __init__(self, invoker: GatewayInvoking) -> None:
        self._invoker = invoker

    def get_candidate_tags(self) -> list:
        return self._invoker.invoke("get_candidate_tags", result_key="candidate_tags", default=[])
