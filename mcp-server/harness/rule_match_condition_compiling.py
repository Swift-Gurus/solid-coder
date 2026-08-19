"""Defines compilation of rule match declarations into workflow conditions."""

from __future__ import annotations

from typing import Protocol

from harness.condition_declaration import ConditionDeclaration
from harness.rule_match_declaration import RuleMatchDeclaration


"""
solid-name: RuleMatchConditionCompiling
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for compiling typed rule applicability into an auditable workflow condition.
"""
class RuleMatchConditionCompiling(Protocol):
    def compile(
        self,
        declaration: RuleMatchDeclaration,
    ) -> ConditionDeclaration | None: ...
