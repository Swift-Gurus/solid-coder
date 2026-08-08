"""Defines parsing of serialized health-check hook context."""

from typing import Optional, Protocol

from findings.hook_context import HookContext


"""
solid-name: HookContextParsing
solid-category: abstraction
solid-description: Contract for parsing serialized hook context into an immutable domain model.
"""
class HookContextParsing(Protocol):
    def parse(self, raw_context: bytes) -> Optional[HookContext]: ...
