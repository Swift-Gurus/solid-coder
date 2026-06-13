"""
solid-description: Evaluates values against configurable severity thresholds.
solid-category: service
solid-tags: [utility, service]
"""

from typing import Any, Protocol


class BandEvaluating(Protocol):
    def evaluate(self, value: Any, bands: dict) -> str: ...


class BandEvaluator:
    """Evaluates a single metric value against a bands dict.

    Supported comparison keys under 'severe' and 'minor':
      greater_than: N           value > N
      greater_than_or_equal: N  value >= N
      less_than: N              value < N
      less_than_or_equal: N     value <= N
      equal: S                  str(value) == S  (frontmatter only, string metrics)

    disabled: true always returns COMPLIANT.
    """

    def evaluate(self, value: Any, bands: dict) -> str:
        if bands.get("disabled"):
            return "COMPLIANT"

        try:
            v = float(value)
        except (TypeError, ValueError):
            equal_val = bands.get("severe", {}).get("equal")
            if equal_val is not None:
                return "SEVERE" if str(value) == str(equal_val) else "COMPLIANT"
            return "COMPLIANT"

        if self._matches(v, bands.get("severe", {})):
            return "SEVERE"
        if self._matches(v, bands.get("minor", {})):
            return "MINOR"
        return "COMPLIANT"

    def _matches(self, v: float, comparison: dict) -> bool:
        if not comparison:
            return False
        if "greater_than" in comparison and v <= comparison["greater_than"]:
            return False
        if "greater_than_or_equal" in comparison and v < comparison["greater_than_or_equal"]:
            return False
        if "less_than" in comparison and v >= comparison["less_than"]:
            return False
        if "less_than_or_equal" in comparison and v > comparison["less_than_or_equal"]:
            return False
        return True
