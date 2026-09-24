"""Calculates a ratio from typed auditable observations."""

from harness.collection_ratio_input import CollectionRatioInput
from harness.collection_ratio_output import CollectionRatioOutput
from harness.ratio_value_calculator import RatioValueCalculator


"""
solid-name: CollectionRatioOperation
solid-category: service
solid-spec: [SPEC-057]
solid-description: Converts included boolean observations into one deterministic ratio operation result.
"""
class CollectionRatioOperation:
    def __init__(self, calculator: RatioValueCalculator) -> None:
        self._calculator = calculator

    def execute(self, input_value: CollectionRatioInput) -> CollectionRatioOutput:
        included = [
            observation
            for observation in input_value.observations
            if observation.included
        ]
        numerator_count = sum(
            1 for observation in included if observation.matches
        )
        denominator_count = len(included)
        return CollectionRatioOutput(
            value=self._calculator.calculate(
                numerator_count,
                denominator_count,
                input_value.empty_value,
            ),
            numerator_count=numerator_count,
            denominator_count=denominator_count,
            used_empty_value=denominator_count == 0,
        )
