"""Defines typed decoding of compact metrics from workflow input."""

from typing import Protocol

from harness.co_located_metric_contract import CoLocatedMetricContract
from harness.output_spec import OutputSpec

"""
solid-name: CoLocatedMetricCollectionDecoding
solid-category: abstraction
solid-spec: [SPEC-058]
solid-description: Contract for decoding co-located measurements against an owning step's typed outputs.
"""


class CoLocatedMetricCollectionDecoding(Protocol):
    def decode(
        self,
        owner_step_id: str,
        outputs: list[OutputSpec],
        value: object,
    ) -> list[CoLocatedMetricContract]: ...
