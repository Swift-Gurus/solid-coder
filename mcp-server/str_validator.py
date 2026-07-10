"""
solid-description: Validator that accepts values supporting string concatenation.
solid-category: utility
"""

from validator_types import DuckTypeValidator


class StrValidator(DuckTypeValidator):
    """Accepts values that support string concatenation (duck-typed str)."""

    def __init__(self) -> None:
        super().__init__(probe=lambda v: v + "", errors=(TypeError,))  # type: ignore[operator]
