"""Evaluates whether one review unit satisfies a rule declaration."""

from harness.rule_applicability_context import RuleApplicabilityContext
from harness.rule_applicability_decision import RuleApplicabilityDecision
from harness.rule_declaration import RuleDeclaration
from harness.rule_selection_evaluating import RuleSelectionEvaluating
from harness.rule_selection_requirement import RuleSelectionRequirement


"""
solid-name: RuleApplicabilityEvaluator
solid-category: service
solid-spec: [SPEC-039]
solid-description: Coordinates extension, unit-kind, and tag applicability decisions for one review rule.
"""
class RuleApplicabilityEvaluator:

    def __init__(
        self,
        selection_evaluator: RuleSelectionEvaluating,
    ) -> None:
        self._selection_evaluator = selection_evaluator

    def evaluate(
        self,
        rule: RuleDeclaration,
        context: RuleApplicabilityContext,
    ) -> RuleApplicabilityDecision:
        extension_decision = self._selection_evaluator.evaluate(
            dimension="file_extensions",
            candidates=[context.file_extension],
            selection=rule.match.file_extensions,
            requirement=RuleSelectionRequirement.ANY,
        )
        if not extension_decision.applicable:
            return extension_decision

        unit_kind_decision = self._selection_evaluator.evaluate(
            dimension="unit_kinds",
            candidates=[context.unit_kind],
            selection=rule.match.unit_kinds,
            requirement=RuleSelectionRequirement.ANY,
        )
        if not unit_kind_decision.applicable:
            return unit_kind_decision

        tag_decision = self._selection_evaluator.evaluate(
            dimension="tags",
            candidates=context.tags,
            selection=rule.match.tags,
            requirement=RuleSelectionRequirement.ALL,
        )
        if not tag_decision.applicable:
            return tag_decision

        return RuleApplicabilityDecision(
            applicable=True,
            dimension="all",
            reason="Every rule matcher dimension matched",
        )
