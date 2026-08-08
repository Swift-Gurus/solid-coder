"""Defines resolution of a requested health-check context file."""

from pathlib import Path
from typing import Protocol


"""
solid-name: HookContextPathResolving
solid-category: abstraction
solid-description: Contract for resolving the hook context path owned by an output directory.
"""
class HookContextPathResolving(Protocol):
    def resolve(self, output_dir: str) -> Path: ...
