"""
solid-description: Contract that defines structural validation of values.
solid-category: abstraction
"""

from typing import Optional, Protocol


class TypeChecking(Protocol):
    """Protocol for a value type validator used by parse_json_field.

    validate() returns the accepted value, or None if the value does not
    conform to the expected structural shape.
    """

    def validate(self, value: object) -> Optional[object]: ...
