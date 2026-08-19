"""Resolves operation outputs from Pydantic result models."""

from typing import Type

from pydantic import BaseModel

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.operation_output_specs_resolving import OperationOutputSpecsResolving
from harness.output_spec import OutputSpec


"""
solid-name: PydanticOperationOutputSpecsResolver
solid-category: boundary
solid-spec: [SPEC-010, SPEC-040]
solid-description: Resolves workflow output specifications from typed result-model schemas.
"""
class PydanticOperationOutputSpecsResolver(OperationOutputSpecsResolving):
    def __init__(
        self,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._error_factory = error_factory

    def resolve(
        self,
        model_type: Type[BaseModel],
    ) -> list[OutputSpec]:
        properties = model_type.model_json_schema().get("properties")
        if not isinstance(properties, dict):
            raise self._error_factory.create(
                f"Operation output model '{model_type.__name__}' has no object properties"
            )
        return [
            OutputSpec(
                name=name,
                type="data",
                schema=properties[name],
            )
            for name in model_type.model_fields
        ]
