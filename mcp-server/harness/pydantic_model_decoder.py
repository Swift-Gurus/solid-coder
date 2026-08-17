"""Decodes structured boundary values with a configured Pydantic model."""

from typing import Generic, Type, TypeVar

from pydantic import BaseModel, ValidationError

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.structured_model_decoding import StructuredModelDecoding

ModelT = TypeVar("ModelT", bound=BaseModel)


"""
solid-name: PydanticModelDecoder
solid-category: service
solid-spec: [SPEC-039]
solid-description: Maps structured boundary values into typed application models and reports schema failures as workflow errors.
"""
class PydanticModelDecoder(StructuredModelDecoding[ModelT], Generic[ModelT]):

    def __init__(
        self,
        model_type: Type[ModelT],
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._model_type = model_type
        self._error_factory = error_factory

    def decode(self, value: object, description: str) -> ModelT:
        try:
            return self._model_type.model_validate(value)
        except ValidationError as error:
            raise self._error_factory.create(
                f"Invalid {description}: {error}"
            ) from error
