"""Decodes structured boundary values with a configured Pydantic model."""

from typing import Generic, TypeVar

from harness.flow_validation_error import FlowValidationError
from harness.structured_model_decoding import StructuredModelDecoding
from pydantic import BaseModel, ValidationError

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
        model_type: type[ModelT],
    ) -> None:
        self._model_type = model_type

    def decode(self, value: object, description: str) -> ModelT:
        try:
            return self._model_type.model_validate(value)
        except ValidationError as error:
            raise FlowValidationError(f"Invalid {description}: {error}") from error
