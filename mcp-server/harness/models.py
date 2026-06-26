"""
solid-description: Defines data model types representing flow specifications and execution state.
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
class ExecutionSpec:
    """
    solid-description: Specifies the execution intent for a step.
    solid-category: model
    """
    intent: str


@dataclass(frozen=True)
class StepDef:
    """
    solid-description: Represents a step definition with configuration, dependencies, and outputs.
    solid-category: model
    """
    id: str
    prompt: str
    depends_on: list[str] = field(default_factory=list)
    outputs: list[OutputSpec] = field(default_factory=list)
    execution: ExecutionSpec | None = None
    for_each: str | None = None


@dataclass(frozen=True)
class FlowDef:
    """
    solid-description: Represents a flow definition with its steps and configuration.
    solid-category: model
    """
    name: str
    max_turns: int
    steps: list[StepDef]


@dataclass(frozen=True)
class StepOutputs:
    """
    solid-description: Represents named outputs produced by a step.
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
    solid-description: Represents the current state of an executing flow.
    solid-category: model
    """
    completed: dict[str, StepOutputs]
    running: list[str]
    turn_count: int
    status: str


@dataclass(frozen=True)
class StepInstance:
    """
    solid-description: Represents an instance of a step execution with iteration context.
    solid-category: model
    """
    step_id: str
    instance_id: str
    item: Any
    prompt: str


@dataclass(frozen=True)
class ValidationResult:
    """
    solid-description: Represents the result of a validation check.
    solid-category: model
    """
    ok: bool
    errors: list[str] = field(default_factory=list)


class FlowValidationError(Exception):
    """
    solid-description: Raised when structural validation of a flow fails.
    solid-category: service
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
