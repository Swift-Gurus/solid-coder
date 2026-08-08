"""Defines lookup of health-check context from an explicitly requested output directory."""

from typing import Optional, Protocol

from findings.hook_context import HookContext


"""
solid-name: RequestedHookContextLoading
solid-category: abstraction
solid-description: Contract for loading hook context owned by a requested output directory.
"""
class RequestedHookContextLoading(Protocol):
    def load(self, output_dir: str) -> Optional[HookContext]: ...
