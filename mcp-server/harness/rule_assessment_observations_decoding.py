"""Defines decoding of completed aggregate rule outputs."""

from typing import Protocol

from harness.rule_assessment_declaration import RuleAssessmentDeclaration
from harness.rule_observations import RuleObservations
from harness.step_outputs import StepOutputs


"""
solid-name: RuleAssessmentObservationsDecoding
solid-category: abstraction
solid-spec: [SPEC-044]
solid-description: Contract for translating one completed aggregate assessment into existing typed rule observations.
"""
class RuleAssessmentObservationsDecoding(Protocol):
    def decode(
        self,
        assessment: RuleAssessmentDeclaration,
        outputs: StepOutputs,
    ) -> RuleObservations: ...
