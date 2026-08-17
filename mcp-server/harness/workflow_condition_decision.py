"""Defines one durable workflow-level condition decision."""

from __future__ import annotations

from dataclasses import dataclass

from harness.condition_declaration import ConditionDeclaration
from harness.condition_evidence import ConditionEvidence


"""
solid-name: WorkflowConditionDecision
solid-category: model
solid-spec: [SPEC-037]
solid-description: Represents the evaluated eligibility of one workflow invocation.
"""
@dataclass(frozen=True)
class WorkflowConditionDecision:
    condition: ConditionDeclaration
    evidence: ConditionEvidence

    @property
    def matched(self) -> bool:
        return self.evidence.matched
