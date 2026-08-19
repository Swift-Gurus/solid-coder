"""Evaluates one typed rule-selection dimension."""

from harness.rule_applicability_decision import (
    RuleApplicabilityDecision,
    RuleMatchDimension,
)
from harness.rule_selection import RuleSelection
from harness.rule_selection_requirement import RuleSelectionRequirement
from harness.rule_value_match_mode import RuleValueMatchMode
from harness.rule_values_matching import RuleValuesMatching
from harness.rule_values_rendering import RuleValuesRendering


"""
solid-name: RuleSelectionEvaluator
solid-category: service
solid-spec: [SPEC-039]
solid-description: Determines applicability for one included/excluded rule-selection dimension.
"""
class RuleSelectionEvaluator:

    def __init__(
        self,
        values_matcher: RuleValuesMatching,
        values_renderer: RuleValuesRendering,
    ) -> None:
        self._values_matcher = values_matcher
        self._values_renderer = values_renderer

    def evaluate(
        self,
        dimension: RuleMatchDimension,
        candidates: list[object],
        selection: RuleSelection,
        requirement: RuleSelectionRequirement,
    ) -> RuleApplicabilityDecision:
        excluded = self._values_matcher.match(
            candidates,
            selection.excluded,
            RuleValueMatchMode.PRESENT,
        )
        if excluded:
            return RuleApplicabilityDecision(
                applicable=False,
                dimension=dimension,
                reason="An excluded value was present",
                decisive_values=self._values_renderer.render(excluded),
            )

        unmatched = self._unmatched_included_values(
            candidates,
            selection.included,
            requirement,
        )
        if unmatched:
            return RuleApplicabilityDecision(
                applicable=False,
                dimension=dimension,
                reason="Required included values did not match",
                decisive_values=self._values_renderer.render(unmatched),
            )

        return RuleApplicabilityDecision(
            applicable=True,
            dimension=dimension,
            reason="Selection matched",
        )

    def _unmatched_included_values(
        self,
        candidates: list[object],
        included: list[object],
        requirement: RuleSelectionRequirement,
    ) -> list[object]:
        if not included:
            return []

        if requirement is RuleSelectionRequirement.ALL:
            return self._values_matcher.match(
                included,
                candidates,
                RuleValueMatchMode.MISSING,
            )

        present = self._values_matcher.match(
            candidates,
            included,
            RuleValueMatchMode.PRESENT,
        )
        return [] if present else included
