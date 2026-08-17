"""Defines structured-input decoding into a typed application model."""

from typing import Generic, Protocol, TypeVar

ModelT = TypeVar("ModelT")


"""
solid-name: StructuredModelDecoding
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for decoding structured boundary values into typed application models.
"""
class StructuredModelDecoding(Protocol, Generic[ModelT]):

    def decode(self, value: object, description: str) -> ModelT:
        ...
