"""Evaluates whether MCP-detected unit tags satisfy one rule declaration."""

from harness.rule_declaration import RuleDeclaration


"""
solid-name: RuleApplicabilityEvaluator
solid-category: service
solid-spec: [SPEC-039]
solid-description: Applies exact all-required tag matching to typed rule metadata and detected unit tags.
"""
class RuleApplicabilityEvaluator:

    def is_applicable(
        self,
        rule: RuleDeclaration,
        detected_tags: list[str],
    ) -> bool:
        return all(tag in detected_tags for tag in rule.tags)
