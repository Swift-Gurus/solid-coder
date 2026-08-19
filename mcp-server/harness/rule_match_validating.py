"""Defines validation of review-rule match declarations."""

from typing import Protocol

from harness.rule_match_declaration import RuleMatchDeclaration


"""
solid-name: RuleMatchValidating
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for validating one typed review-rule match declaration before execution.
"""
class RuleMatchValidating(Protocol):

    def validate(self, declaration: RuleMatchDeclaration) -> None: ...
