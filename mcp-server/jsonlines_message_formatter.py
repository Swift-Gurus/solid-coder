"""
solid-name: JsonlinesMessageFormatter
solid-category: service
solid-description: Serializes a message to bytes.
"""

from json_serializer import JsonSerializer, JsonSerializing
from jsonlines_message_formatting import JsonlinesMessageFormatting


class JsonlinesMessageFormatter(JsonlinesMessageFormatting):

    def __init__(self, serializer: JsonSerializing = None) -> None:
        self._serializer = serializer or JsonSerializer()

    def format(self, msg: dict) -> bytes:
        return self._serializer.serialize(msg).encode("utf-8") + b"\n"