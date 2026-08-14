"""Defines process termination at command-line boundaries."""

from typing import Protocol


"""
solid-name: ProcessExiting
solid-category: abstraction
solid-description: Contract for terminating a command-line process with a status code.
"""
class ProcessExiting(Protocol):
    def exit(self, status: int) -> None: ...
