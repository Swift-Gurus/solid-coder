"""Reads the current process directory for agent-start fallback context."""

import os
from typing import Protocol


"""
solid-name: CurrentDirectoryReading
solid-category: abstraction
solid-description: Contract for reading the current process directory.
"""
class CurrentDirectoryReading(Protocol):
    def read(self) -> str: ...


"""
solid-name: ProcessCurrentDirectoryReader
solid-category: boundary
solid-description: Reads the current directory from the host process.
"""
class ProcessCurrentDirectoryReader(CurrentDirectoryReading):
    def read(self) -> str:
        return os.getcwd()
