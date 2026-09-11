"""Defines model-visible workflow applicability for one item."""

from dataclasses import dataclass, field


"""
solid-name: AggregateItemAssignment
solid-category: model
solid-spec: [SPEC-045]
solid-description: Associates one opaque item label with its ordered applicable workflow aliases.
"""
@dataclass(frozen=True)
class AggregateItemAssignment:
    label: str
    workflow_aliases: list[str] = field(default_factory=list)
