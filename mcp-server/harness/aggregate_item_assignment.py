"""Defines model-visible workflow applicability for one item."""

from dataclasses import dataclass, field

"""
solid-name: AggregateItemAssignment
solid-category: model
solid-spec: [SPEC-045]
solid-description: Represents the workflows applicable to an individual item.
"""


@dataclass(frozen=True)
class AggregateItemAssignment:
    label: str
    workflow_aliases: list[str] = field(default_factory=list)
