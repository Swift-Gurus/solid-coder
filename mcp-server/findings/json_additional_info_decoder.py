"""Decodes stored measurement context at the JSON boundary."""

from typing import Optional

from findings.additional_info_decoding import AdditionalInfoDecoding
from findings.additional_info_value import AdditionalInfoValue
from health.llama.json_deserializer import JsonDeserializing


"""
solid-name: JsonAdditionalInfoDecoder
solid-category: boundary-adapter
solid-description: Decodes JSON-encoded measurement context into a typed contextual value.
"""
class JsonAdditionalInfoDecoder(AdditionalInfoDecoding):
    def __init__(self, deserializer: JsonDeserializing) -> None:
        self._deserializer = deserializer

    def decode(self, encoded_value: str) -> Optional[AdditionalInfoValue]:
        wrapper = self._deserializer.deserialize(encoded_value.encode("utf-8"))
        if wrapper is None or "value" not in wrapper:
            return None
        return AdditionalInfoValue(wrapper["value"])
