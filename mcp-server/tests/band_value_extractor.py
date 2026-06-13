"""
solid-description: Derives representative SEVERE and COMPLIANT test values from a metric's bands dict.
solid-category: unit-test
"""

from typing import Any


class BandValueExtractor:
    """Derives test values from a bands dict without hardcoding thresholds."""

    def severe_value(self, bands: dict) -> Any:
        """Return a value that should trigger SEVERE given this bands dict."""
        severe = bands.get("severe", {})
        if "equal" in severe:
            return severe["equal"]
        if "greater_than_or_equal" in severe:
            return severe["greater_than_or_equal"]
        if "greater_than" in severe:
            return severe["greater_than"] + 1
        if "less_than" in severe:
            return severe["less_than"] - 1
        if "less_than_or_equal" in severe:
            return severe["less_than_or_equal"]
        return None

    def compliant_value(self, bands: dict) -> Any:
        """Return a value that should be COMPLIANT given this bands dict."""
        severe = bands.get("severe", {})
        if "equal" in severe:
            return "other"
        if "greater_than_or_equal" in severe:
            return max(0, severe["greater_than_or_equal"] - 1)
        if "greater_than" in severe:
            return severe["greater_than"]
        if "less_than" in severe:
            return severe["less_than"]
        if "less_than_or_equal" in severe:
            return severe["less_than_or_equal"] + 1
        return 0

    def numeric_severe_op(self, bands: dict):
        """Return (op, threshold) for the first numeric 'greater_than*' severe comparator, or None."""
        severe = bands.get("severe", {})
        for op in ("greater_than_or_equal", "greater_than"):
            if op in severe:
                return op, severe[op]
        return None, None
