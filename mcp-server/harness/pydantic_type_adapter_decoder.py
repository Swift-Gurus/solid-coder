"""Decodes schema types that are not standalone Pydantic models."""

from typing import Generic, TypeVar

from pydantic import TypeAdapter, ValidationError

from harness.flow_validation_error import FlowValidationError
from harness.structured_model_decoding import StructuredModelDecoding

ValueT = TypeVar("ValueT")


"""
solid-name: PydanticTypeAdapterDecoder
solid-category: boundary
solid-spec: [SPEC-059]
solid-description: Decodes structured workflow inputs against union or collection schemas with actionable validation errors.
"""
class PydanticTypeAdapterDecoder(StructuredModelDecoding[ValueT], Generic[ValueT]):
    def __init__(self, adapter: TypeAdapter[ValueT]) -> None:
        self._adapter = adapter

    def decode(self, value: object, description: str) -> ValueT:
        try:
            return self._adapter.validate_python(value)
        except ValidationError as error:
            raise FlowValidationError(f"Invalid {description}: {error}") from error
