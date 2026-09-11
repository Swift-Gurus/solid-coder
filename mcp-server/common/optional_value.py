"""Provides functional operations over a nullable value."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar


Value = TypeVar("Value")
MappedValue = TypeVar("MappedValue")


"""
solid-name: OptionalValue
solid-category: value
solid-description: Chains typed transformations and side effects without exposing repeated nullable-value branches.
"""
@dataclass(frozen=True)
class OptionalValue(Generic[Value]):
    _value: Value | None

    @classmethod
    def from_nullable(cls, value: Value | None) -> OptionalValue[Value]:
        return cls(value)

    def map(
        self,
        transform: Callable[[Value], MappedValue | None],
    ) -> OptionalValue[MappedValue]:
        if self._value is None:
            return OptionalValue.from_nullable(None)
        return OptionalValue.from_nullable(transform(self._value))

    def flat_map(
        self,
        transform: Callable[[Value], OptionalValue[MappedValue]],
    ) -> OptionalValue[MappedValue]:
        if self._value is None:
            return OptionalValue.from_nullable(None)
        return transform(self._value)

    def do(self, effect: Callable[[Value], None]) -> OptionalValue[Value]:
        if self._value is not None:
            effect(self._value)
        return self

    def on_none(self, effect: Callable[[], None]) -> OptionalValue[Value]:
        if self._value is None:
            effect()
        return self

    def value_or(self, fallback: Value) -> Value:
        return fallback if self._value is None else self._value
