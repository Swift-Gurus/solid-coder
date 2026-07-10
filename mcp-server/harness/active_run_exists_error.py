"""
solid-name: ActiveRunExistsError
solid-category: model
solid-spec: [SPEC-013]
solid-description: Exception raised when starting a flow while one is already active.
"""

from __future__ import annotations


class ActiveRunExistsError(Exception):

    def __init__(self, run_id: str) -> None:
        super().__init__(f"Flow run already active: {run_id}")
        self.run_id = run_id
