"""Defines an immutable decoded additional-information value."""

from dataclasses import dataclass


"""
solid-name: AdditionalInfoValue
solid-category: model
solid-description: Represents successfully decoded contextual information attached to a review measurement.
"""
@dataclass(frozen=True)
class AdditionalInfoValue:
    value: object
