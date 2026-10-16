"""Resolves operation outputs from Pydantic result models."""

from typing import Type

from pydantic import BaseModel, JsonValue

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.operation_output_specs_resolving import OperationOutputSpecsResolving
from harness.output_spec import OutputSpec
from harness.structured_model_decoding import StructuredModelDecoding
from harness.workflow_data_schema import WorkflowDataSchema


"""
solid-name: PydanticOperationOutputSpecsResolver
solid-category: boundary
solid-spec: [SPEC-010, SPEC-040, SPEC-057]
solid-description: Resolves workflow output specifications with addressable nested fields and retained recursive schema definitions.
"""
class PydanticOperationOutputSpecsResolver(OperationOutputSpecsResolving):
    def __init__(
        self,
        error_factory: FlowValidationErrorCreating,
        schema_expander: StructuredModelDecoding[JsonValue],
        schema_decoder: StructuredModelDecoding[WorkflowDataSchema],
    ) -> None:
        self._error_factory = error_factory
        self._schema_expander = schema_expander
        self._schema_decoder = schema_decoder

    def resolve(
        self,
        model_type: Type[BaseModel],
    ) -> list[OutputSpec]:
        description = f"operation output model '{model_type.__name__}'"
        expanded = self._schema_expander.decode(model_type.model_json_schema(by_alias=False), description)
        schema = self._schema_decoder.decode(expanded, description)
        if schema.type != "object":
            raise self._error_factory.create(
                f"Operation output model '{model_type.__name__}' has no object properties"
            )
        definitions = {
            name: definition.model_dump(by_alias=True, exclude_unset=True)
            for name, definition in schema.definitions.items()
        }
        outputs: list[OutputSpec] = []
        for name in model_type.model_fields:
            property_schema = schema.property(name)
            if property_schema is None:
                raise self._error_factory.create(f"Operation output model '{model_type.__name__}' has no schema for '{name}'")
            serialized = property_schema.model_dump(by_alias=True, exclude_unset=True)
            outputs.append(OutputSpec(
                name=name,
                type="data",
                schema={**serialized, "$defs": definitions} if definitions else serialized,
            ))
        return outputs
