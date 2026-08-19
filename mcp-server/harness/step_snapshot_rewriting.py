"""Defines public YAML rewriting for typed workflow steps."""

from typing import Protocol

from harness.step_def import StepDef


"""
solid-name: StepSnapshotRewriting
solid-category: abstraction
solid-spec: [SPEC-031, SPEC-039, SPEC-040]
solid-description: Contract for rewriting typed step snapshots into public workflow YAML grammar.
"""
class StepSnapshotRewriting(Protocol):
    def rewrite(self, snapshot: dict, step: StepDef) -> None: ...
