"""
solid-description: Contract for converting input data into step specifications.
solid-category: abstraction
"""

from __future__ import annotations

from typing import Protocol

from harness.models import ExecutionSpec, OutputSpec, StepDef


class StepBuilding(Protocol):
    """
    solid-description: Contract for converting input data into step specifications.
    solid-category: abstraction
    """

    def build(self, raw: dict) -> StepDef: ...


class StepBuilder:
    """
    solid-description: Transforms input data into executable step specifications.
    solid-category: service
    """

    def build(self, raw: dict) -> StepDef:
        raw_outputs = raw.get("outputs") or []
        outputs = [
            OutputSpec(
                name=o["name"],
                type=o["type"],
                schema=o.get("schema"),
                schema_file=o.get("schema_file"),
            )
            for o in raw_outputs
        ]

        raw_exec = raw.get("execution")
        execution = ExecutionSpec(intent=raw_exec["intent"]) if raw_exec else None

        return StepDef(
            id=raw["id"],
            prompt=raw.get("prompt") or "",
            depends_on=raw.get("depends_on") or [],
            outputs=outputs,
            execution=execution,
            for_each=raw.get("for_each"),
            type=raw.get("type", "agent"),
            prompt_file=raw.get("prompt_file"),
            command=raw.get("command"),
            timeout_seconds=raw.get("timeout_seconds"),
            max_attempts=raw.get("max_attempts", 3),
        )
