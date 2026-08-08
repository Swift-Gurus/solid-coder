"""
solid-name: RunContextBuilding
solid-category: abstraction
solid-spec: [SPEC-031]
solid-description: Contract for building a context dictionary from run state and parameters.
"""

from __future__ import annotations

from typing import Any, Protocol

from harness.models import RunState


class RunContextBuilding(Protocol):

    def build(self, params: dict, run_state: RunState) -> dict[str, Any]: ...
