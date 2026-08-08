"""Defines decoding of measurement additional information."""

from typing import Optional, Protocol

from findings.additional_info_value import AdditionalInfoValue


"""
solid-name: AdditionalInfoDecoding
solid-category: abstraction
solid-description: Contract for decoding stored measurement context into a typed value.
"""
class AdditionalInfoDecoding(Protocol):
    def decode(self, encoded_value: str) -> Optional[AdditionalInfoValue]: ...
