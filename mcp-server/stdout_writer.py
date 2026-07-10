"""
solid-description: Serialises a payload and writes it to an injectable output stream.
solid-category: utility
"""

import sys
from typing import IO, Callable

from json_serializer import JsonSerializer, JsonSerializing


class StdoutWriter:
    """Adapter: serialises payload to JSON and writes to an injectable stream.

    The stream_factory is resolved lazily at write time so that redirect_stdout
    in tests is respected without eager capture.
    """

    def __init__(
        self,
        stream_factory: Callable[[], IO] = lambda: sys.stdout,
        serializer: JsonSerializing = JsonSerializer(),
    ) -> None:
        self._stream_factory = stream_factory
        self._serializer = serializer

    def write_payload(self, payload: dict) -> None:
        stream = self._stream_factory()
        stream.write(self._serializer.serialize(payload))
        stream.flush()