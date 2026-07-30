"""
solid-name: ActiveRunLockClearing
solid-category: abstraction
solid-spec: [SPEC-013]
solid-description: Contract for clearing an active run so subsequent operations can proceed.
"""

from __future__ import annotations

from typing import Protocol


class ActiveRunLockClearing(Protocol):
    def clear(self, run_id: str) -> str: ...
