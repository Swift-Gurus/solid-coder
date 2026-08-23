"""Compiles typed rule applicability into reusable workflow conditions."""

from __future__ import annotations

from harness.all_condition import AllCondition
from harness.condition_declaration import ConditionDeclaration
from harness.condition_operator import ConditionOperator
from harness.rule_match_condition_compiling import RuleMatchConditionCompiling
from harness.rule_match_declaration import RuleMatchDeclaration
from harness.rule_selection_condition_compiling import (
    RuleSelectionConditionCompiling,
)


"""
solid-name: RuleMatchConditionCompiler
solid-category: service
solid-spec: [SPEC-039]
solid-description: Compiles exact extension, unit-kind, and tag selectors into auditable workflow conditions.
"""
class RuleMatchConditionCompiler(RuleMatchConditionCompiling):
    _UNIT_REFERENCE = "params.review_unit.applicability.unit_kind"
    _EXTENSION_REFERENCE = "params.review_unit.applicability.file_extension"
    _TAGS_REFERENCE = "params.review_unit.applicability.tags"

    def __init__(
        self,
        selection_compiler: RuleSelectionConditionCompiling,
    ) -> None:
        self._selection_compiler = selection_compiler

    def compile(
        self,
        declaration: RuleMatchDeclaration,
    ) -> ConditionDeclaration | None:
        conditions = [
            *self._selection_compiler.compile(
                self._EXTENSION_REFERENCE,
                declaration.file_extensions.included,
                declaration.file_extensions.excluded,
                ConditionOperator.IN,
                ConditionOperator.NOT_IN,
            ),
            *self._selection_compiler.compile(
                self._UNIT_REFERENCE,
                [kind.value for kind in declaration.unit_kinds.included],
                [kind.value for kind in declaration.unit_kinds.excluded],
                ConditionOperator.IN,
                ConditionOperator.NOT_IN,
            ),
            *self._selection_compiler.compile(
                self._TAGS_REFERENCE,
                list(declaration.tags.included),
                list(declaration.tags.excluded),
                ConditionOperator.CONTAINS,
                ConditionOperator.NOT_CONTAINS,
            ),
        ]
        if not conditions:
            return None
        return AllCondition(conditions=tuple(conditions))
