"""
solid-name: StartupContextResolving
solid-category: abstraction
solid-spec: [SPEC-013]
solid-description: Contract for resolving startup context.
"""

from __future__ import annotations

from typing import Protocol

from harness.startup_context import StartupContext


class StartupContextResolving(Protocol):

    def resolve(self) -> StartupContext: ...