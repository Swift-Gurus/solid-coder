"""
solid-description: Accepts values for which a probe function succeeds without raising.
solid-category: utility
"""

from collections.abc import Callable


class DuckTypeValidator:
    """TypeChecking: accepts values for which `probe(value)` succeeds without raising.

    Wraps the check-then-return-or-None pattern shared by all duck-typed
    validators, parameterized by the specific capability probe and the
    exception type(s) that signal an unsupported value.
    """

    def __init__(
        self, probe: Callable[[object], object], errors: tuple[type[BaseException], ...]
    ) -> None:
        self._probe = probe
        self._errors = errors

    def validate(self, value: object) -> object | None:
        try:
            self._probe(value)
            return value
        except self._errors:
            return None
