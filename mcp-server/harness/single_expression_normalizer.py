"""Normalizes a single wrapped workflow expression."""

import re

from harness.expression_normalizing import ExpressionNormalizing


_SINGLE_EXPRESSION = re.compile(r"^\{\{([^}]+)\}\}$")


"""
solid-name: SingleExpressionNormalizer
solid-category: service
solid-spec: [SPEC-030, SPEC-037]
solid-description: Removes the optional template wrapper from one workflow expression.
"""
class SingleExpressionNormalizer(ExpressionNormalizing):
    def normalize(self, expression: str) -> str:
        stripped = expression.strip()
        match = _SINGLE_EXPRESSION.match(stripped)
        return match.group(1).strip() if match else stripped
