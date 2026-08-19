"""Defines output-contract resolution for registered operations."""

from typing import Protocol, Type

from pydantic import BaseModel

from harness.output_spec import OutputSpec


"""
solid-name: OperationOutputSpecsResolving
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-040]
solid-description: Contract for resolving workflow output specifications from a typed operation result model.
"""
class OperationOutputSpecsResolving(Protocol):
    def resolve(
        self,
        model_type: Type[BaseModel],
    ) -> list[OutputSpec]: ...
