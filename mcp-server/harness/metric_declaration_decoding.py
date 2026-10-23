"""Defines typed metric-declaration decoding at the workflow boundary."""

from typing import Protocol

from harness.metric_step_contract import MetricStepContract

"""
solid-name: MetricDeclarationDecoding
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for decoding one workflow metric step into its typed metric declaration.
"""


class MetricDeclarationDecoding(Protocol):
    def decode(self, raw: dict) -> MetricStepContract: ...
