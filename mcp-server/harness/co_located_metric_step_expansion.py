"""Defines canonical metric steps expanded from one owner."""

from dataclasses import dataclass

from harness.co_located_metric_identity import CoLocatedMetricIdentity
from harness.step_declaration import StepDeclaration

"""
solid-name: CoLocatedMetricStepExpansion
solid-category: model
solid-spec: [SPEC-058]
solid-description: Represents generated metric declarations with guaranteed canonical step identifiers.
"""


@dataclass(frozen=True)
class CoLocatedMetricStepExpansion:
    steps: list[StepDeclaration]
    step_ids: list[str]
    identities: list[CoLocatedMetricIdentity]
