"""Parses workflow for-each references."""

from __future__ import annotations

import re

from harness.for_each_reference import ForEachReference
from harness.for_each_reference_parsing import ForEachReferenceParsing
from harness.models import FlowValidationError

_REFERENCE = re.compile(
    r"^\{\{\s*steps\.([^.\s]+)\.outputs\.([^.\s}]+)\s*\}\}$"
)


"""
solid-name: ForEachReferenceParser
solid-category: service
solid-spec: [SPEC-010, SPEC-030]
solid-description: Parses and validates workflow for-each source-output expression syntax.
"""
class ForEachReferenceParser(ForEachReferenceParsing):
    def parse(self, step_id: str, expression: str) -> ForEachReference:
        match = _REFERENCE.fullmatch(expression.strip())
        if match is None:
            raise FlowValidationError(
                f"Step '{step_id}' for_each must use steps.<id>.outputs.<name>"
            )
        return ForEachReference(
            step_id=match.group(1),
            output_name=match.group(2),
        )
