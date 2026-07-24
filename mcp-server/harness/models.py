"""
solid-description: Specifies flows and tracks their execution.
solid-category: model
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class OutputSpec:
    """
    solid-description: Specifies a named output produced by a step.
    solid-category: model
    """
    name: str
    type: str
    schema: dict | None = None
    schema_file: str | None = None


@dataclass(frozen=True)
class StepDef:
    """
    solid-description: Defines a step in a flow with its configuration, dependencies, and outputs.
    solid-category: model
    """
    id: str
    prompt: str
    depends_on: list[str] = field(default_factory=list)
    outputs: list[OutputSpec] = field(default_factory=list)
    for_each: str | None = None
    type: str = "agent"
    mode: str | None = None
    prompt_file: str | None = None
    command: list[str] | None = None
    timeout_seconds: int | None = None
    max_attempts: int = 3


@dataclass(frozen=True)
class FlowDef:
    """
    solid-description: Defines a flow including its steps and execution constraints.
    solid-category: model
    """
    name: str
    max_turns: int
    steps: list[StepDef]


@dataclass(frozen=True)
class StepOutputs:
    """
    solid-description: Provides access to named output values.
    solid-category: model
    """
    values: dict[str, Any] = field(default_factory=dict)

    def get(self, name: str) -> Any:
        return self.values.get(name)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.values)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "StepOutputs":
        return cls(values=dict(d))


@dataclass(frozen=True)
class RunState:
    """
    solid-description: Tracks the execution state and progress of a running flow.
    solid-category: model
    """
    completed: dict[str, StepOutputs]
    running: list[str]
    turn_count: int
    status: str
    attempts_used: dict[str, int] = field(default_factory=dict)
    rejection_reasons: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class StepInstance:
    """
    solid-description: Provides the execution context of a step instance within an iteration.
    solid-category: model
    """
    step_id: str
    instance_id: str
    item: Any
    prompt: str


@dataclass(frozen=True)
class ValidationResult:
    """
    solid-description: Communicates whether a validation check passed and any errors.
    solid-category: model
    """
    ok: bool
    errors: list[str] = field(default_factory=list)


class FlowValidationError(Exception):
    """
    solid-description: Indicates a flow structure validation failure.
    solid-category: service
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
