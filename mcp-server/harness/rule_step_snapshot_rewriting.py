"""Defines public snapshot rewriting for typed rule steps."""

from typing import Protocol

from harness.step_def import StepDef


"""
solid-name: RuleStepSnapshotRewriting
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for rewriting typed rule-step snapshots into their public workflow YAML grammar.
"""
class RuleStepSnapshotRewriting(Protocol):
    def rewrite(self, snapshot: dict, step: StepDef) -> None: ...
