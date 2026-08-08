"""
solid-name: IsolatedRunPathResolving
solid-category: abstraction
solid-spec: [SPEC-031]
solid-description: Contract for resolving isolation-aware base directories.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from harness.startup_context import StartupContext


class IsolatedRunPathResolving(Protocol):
    def provisioning_base_dir(self, startup: StartupContext, isolated: bool) -> Path: ...

    def effective_base_dir(self, base_dir: Path, run_dir: Path, isolated: bool) -> Path: ...