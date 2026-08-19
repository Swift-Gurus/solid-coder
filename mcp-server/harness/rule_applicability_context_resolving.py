"""Defines rule-applicability context resolution from source analysis."""

from typing import Protocol

from harness.rule_applicability_context import RuleApplicabilityContext
from source.source_analysis import SourceAnalysis
from source.source_unit import SourceUnit


"""
solid-name: RuleApplicabilityContextResolving
solid-category: abstraction
solid-spec: [SPEC-039, SPEC-040]
solid-description: Contract for resolving one review unit's typed rule-applicability context from source analysis.
"""
class RuleApplicabilityContextResolving(Protocol):

    def resolve(
        self,
        analysis: SourceAnalysis,
        unit: SourceUnit,
    ) -> RuleApplicabilityContext: ...
