"""
solid-description: Validates values supporting mutable sequence operations.
solid-category: utility
"""

from validator_types import DuckTypeValidator


class ListValidator(DuckTypeValidator):
    """Accepts values that support mutable sequence append (duck-typed list)."""

    def __init__(self) -> None:
        super().__init__(probe=lambda v: v.append, errors=(AttributeError,))  # type: ignore[union-attr]
