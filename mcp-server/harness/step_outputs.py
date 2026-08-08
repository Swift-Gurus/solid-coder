"""Defines the recorded values produced by one completed step."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


"""
solid-name: StepOutputs
solid-category: model
solid-spec: [SPEC-030]
solid-description: Provides immutable access to the named values recorded for one completed workflow step.
"""
@dataclass(frozen=True)
class StepOutputs:
    values: dict[str, Any] = field(default_factory=dict)

    def get(self, name: str) -> Any:
        return self.values.get(name)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.values)
