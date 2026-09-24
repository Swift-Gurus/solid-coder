"""Calculates one ratio from deterministic counts."""


"""
solid-name: RatioValueCalculator
solid-category: service
solid-spec: [SPEC-054, SPEC-057]
solid-description: Shares zero-denominator and division semantics between ratio reducers and operations.
"""
class RatioValueCalculator:
    def calculate(
        self,
        numerator_count: int,
        denominator_count: int,
        empty_value: float,
    ) -> float:
        if denominator_count == 0:
            return empty_value
        return numerator_count / denominator_count
