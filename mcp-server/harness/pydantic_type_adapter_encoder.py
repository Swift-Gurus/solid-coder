"""Encodes typed models at structured output boundaries."""

from typing import Generic, Protocol, TypeVar

from pydantic import TypeAdapter

ValueT = TypeVar("ValueT", contravariant=True)


"""
solid-name: StructuredModelEncoding
solid-category: abstraction
solid-spec: [SPEC-059]
solid-description: Contract for encoding typed application models into structured boundary values.
"""
class StructuredModelEncoding(Protocol[ValueT]):
    def encode(self, value: ValueT) -> object: ...


"""
solid-name: PydanticTypeAdapterEncoder
solid-category: adapter
solid-spec: [SPEC-059]
solid-description: Encodes validated application models as JSON-compatible structured boundary values.
"""
class PydanticTypeAdapterEncoder(StructuredModelEncoding[ValueT], Generic[ValueT]):
    def __init__(self, adapter: TypeAdapter[ValueT]) -> None:
        self._adapter = adapter

    def encode(self, value: ValueT) -> object:
        return self._adapter.dump_python(value, mode="json")
