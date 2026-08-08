"""Defines ownership validation for requested health-check context."""

from typing import Protocol

from findings.hook_context import HookContext


"""
solid-name: HookContextOwnershipValidating
solid-category: abstraction
solid-description: Contract for verifying that hook context belongs to a requested output directory.
"""
class HookContextOwnershipValidating(Protocol):
    def is_owned(self, context: HookContext, output_dir: str) -> bool: ...
