"""Encodes typed models at structured output boundaries."""

from typing import Generic, Protocol, TypeVar

from pydantic import TypeAdapter

ValueT_contra = TypeVar("ValueT_contra", contravariant=True)


"""
solid-name: StructuredModelEncoding
solid-category: abstraction
solid-spec: [SPEC-059]
solid-description: Contract for encoding typed application models into structured boundary values.
"""


class StructuredModelEncoding(Protocol[ValueT_contra]):
    def encode(self, value: ValueT_contra) -> object: ...


"""
solid-name: PydanticTypeAdapterEncoder
solid-category: adapter
solid-spec: [SPEC-059]
solid-description: Encodes validated application models as JSON-compatible structured boundary values.
"""


class PydanticTypeAdapterEncoder(
    StructuredModelEncoding[ValueT_contra], Generic[ValueT_contra]
):
    def __init__(self, adapter: TypeAdapter[ValueT_contra]) -> None:
        self._adapter = adapter

    def encode(self, value: ValueT_contra) -> object:
        return self._adapter.dump_python(value, mode="json")
