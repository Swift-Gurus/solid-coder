"""Defines sibling identity for one aggregate model turn."""

from dataclasses import dataclass


"""
solid-name: AggregateBatchStepGroupIdentity
solid-category: model
solid-spec: [SPEC-045]
solid-description: Identifies original workflow steps presented together in one aggregate model turn.
"""
@dataclass(frozen=True)
class AggregateBatchStepGroupIdentity:
    presentation_boundary_id: str
