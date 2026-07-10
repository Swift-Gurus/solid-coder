"""
solid-description: Accepts objects that conform to the violation data structure.
solid-category: utility
"""

from validator_types import DuckTypeValidator


class ViolationDictValidator(DuckTypeValidator):
    """Accepts objects that have string principle, issue, and fix fields.

    Validates structural shape of LLM violation dicts from external JSON output.
    """

    def __init__(self) -> None:
        super().__init__(
            probe=lambda v: (v["principle"] + "", v["issue"] + "", v["fix"] + ""),  # type: ignore[index,operator]
            errors=(KeyError, TypeError),
        )
