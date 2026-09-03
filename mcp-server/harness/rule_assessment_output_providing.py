"""Defines aggregate rule-assessment output contract generation."""

from typing import Protocol

from harness.output_spec import OutputSpec
from harness.rule_assessment_declaration import RuleAssessmentDeclaration


"""
solid-name: RuleAssessmentOutputProviding
solid-category: abstraction
solid-spec: [SPEC-044]
solid-description: Contract for generating audited workflow outputs from one typed aggregate assessment declaration.
"""
class RuleAssessmentOutputProviding(Protocol):
    def provide(
        self,
        assessment: RuleAssessmentDeclaration,
    ) -> list[OutputSpec]: ...
