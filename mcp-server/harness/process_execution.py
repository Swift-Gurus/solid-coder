"""Defines a typed subprocess execution request."""

from typing import Protocol


"""
solid-name: ProcessExecution
solid-category: abstraction
solid-spec: [SPEC-035]
solid-description: Contract for supplying an ordered subprocess argument list without shell reconstruction.
"""
class ProcessExecution(Protocol):
    def process_arguments(self) -> list[str]: ...
