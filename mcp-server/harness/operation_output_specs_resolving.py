"""Defines output-contract resolution for registered operations."""

from typing import Protocol

from harness.output_spec import OutputSpec
from pydantic import BaseModel

"""
solid-name: OperationOutputSpecsResolving
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-040]
solid-description: Contract for resolving workflow output specifications from a typed operation result model.
"""


class OperationOutputSpecsResolving(Protocol):
    def resolve(
        self,
        model_type: type[BaseModel],
    ) -> list[OutputSpec]: ...
