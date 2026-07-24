"""
solid-name: ActiveRunLocating
solid-category: abstraction
solid-spec: [SPEC-013]
solid-description: Contract for locating the currently active run.
"""

from __future__ import annotations

from typing import Protocol

from harness.active_run_location import ActiveRunLocation


class ActiveRunLocating(Protocol):

    def locate(self, run_id: str | None = None) -> ActiveRunLocation: ...