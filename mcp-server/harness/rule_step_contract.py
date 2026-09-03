"""Defines the resolved rule-specific portion of one workflow step."""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.metric_declaration import MetricDeclaration
from harness.output_spec import OutputSpec
from harness.rule_assessment_declaration import RuleAssessmentDeclaration


"""
solid-name: RuleStepContract
solid-category: model
solid-spec: [SPEC-039]
solid-description: Carries typed metric metadata and the output contract resolved for one workflow step.
"""
@dataclass(frozen=True)
class RuleStepContract:
    outputs: list[OutputSpec] = field(default_factory=list)
    metric: MetricDeclaration | None = None
    assessment: RuleAssessmentDeclaration | None = None
