"""Resolves an optional structured mode with an inherited typed default."""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from typing import Generic, Protocol, TypeVar

from harness.structured_model_decoding import StructuredModelDecoding


Mode = TypeVar("Mode")


"""
solid-name: ModeDeclaration
solid-category: abstraction
solid-spec: [SPEC-045]
solid-description: Contract for structured declarations that expose a typed mode.
"""
class ModeDeclaration(Protocol[Mode]):
    mode: Mode


Declaration = TypeVar("Declaration", bound=ModeDeclaration)


"""
solid-name: StructuredModeResolver
solid-category: service
solid-spec: [SPEC-045]
solid-description: Resolves one explicitly authored structured mode or returns its inherited typed default.
"""
class StructuredModeResolver(Generic[Declaration, Mode]):
    def __init__(
        self,
        decoder: StructuredModelDecoding[Declaration],
        field: str,
        description: str,
    ) -> None:
        self._decoder = decoder
        self._field = field
        self._description = description

    def resolve(self, raw: Mapping[str, object], default: Mode) -> Mode:
        value = raw.get(self._field)
        if value is None:
            return default
        if isinstance(default, Enum) and isinstance(value, str):
            return type(default)(value)
        return self._decoder.decode(value, self._description).mode
