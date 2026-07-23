"""
solid-name: FlowGraphValidating
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for validating flow step definitions for structural integrity.
"""

from __future__ import annotations

from typing import Protocol

from harness.for_each_reference_validator import ForEachReferenceValidating
from harness.include_structure_validator import IncludeStructureValidating
from harness.models import StepDef
from harness.step_graph_validator import StepGraphValidating


class FlowGraphValidating(Protocol):
    """
    solid-name: FlowGraphValidating
    solid-category: abstraction
    solid-spec: [SPEC-027]
    solid-description: Contract for validating flow step definitions for structural integrity.
    """

    def validate_raw(self, steps: list[dict], alias_groups: dict[str, list[str]] | None = None) -> None: ...
    def validate_for_each_references(self, steps: list[StepDef]) -> None: ...
    def validate_includes(
        self,
        steps: list[dict],
        alias_groups: dict[str, list[str]],
        top_level_step_ids: set[str],
        include_chain: list[str],
    ) -> None: ...


class FlowGraphValidator:
    """
    solid-name: FlowGraphValidator
    solid-category: service
    solid-spec: [SPEC-027]
    solid-description: Validates flow step definitions for structural integrity.
    """

    def __init__(
        self,
        step_graph_validator: StepGraphValidating,
        include_structure_validator: IncludeStructureValidating,
        for_each_validator: ForEachReferenceValidating,
    ) -> None:
        self._step_graph_validator = step_graph_validator
        self._include_structure_validator = include_structure_validator
        self._for_each_validator = for_each_validator

    def validate_raw(self, steps: list[dict], alias_groups: dict[str, list[str]] | None = None) -> None:
        self._step_graph_validator.validate_raw(steps, alias_groups)

    def validate_includes(
        self,
        steps: list[dict],
        alias_groups: dict[str, list[str]],
        top_level_step_ids: set[str],
        include_chain: list[str],
    ) -> None:
        self._include_structure_validator.validate_includes(steps, alias_groups, top_level_step_ids, include_chain)

    def validate_for_each_references(self, steps: list[StepDef]) -> None:
        self._for_each_validator.validate_for_each_references(steps)
