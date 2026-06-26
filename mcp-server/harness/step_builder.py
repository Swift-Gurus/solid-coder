"""
solid-description: Contract for constructing StepDef instances from raw step dictionaries.
solid-category: abstraction
"""

from __future__ import annotations

from typing import Protocol

from harness.models import ExecutionSpec, OutputSpec, StepDef


class StepBuilding(Protocol):
    """
    solid-description: Contract for building a StepDef from a raw step dictionary.
    solid-category: abstraction
    """

    def build(self, raw: dict) -> StepDef: ...


class StepBuilder:
    """
    solid-description: Builds StepDef instances from raw step dictionaries.
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
            prompt=raw["prompt"],
            depends_on=raw.get("depends_on") or [],
            outputs=outputs,
            execution=execution,
            for_each=raw.get("for_each"),
        )
