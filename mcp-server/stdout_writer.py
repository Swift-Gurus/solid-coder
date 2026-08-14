"""
solid-description: Serialises a payload and writes it to an injectable output stream.
solid-category: utility
"""

import sys
from typing import IO, Callable

from gateway_output_writing import GatewayOutputWriting
from json_serializer import JsonSerializer, JsonSerializing


"""
solid-name: StdoutWriter
solid-category: utility
solid-description: Delivers serialized payloads and results to a configurable output destination.
"""
class StdoutWriter(GatewayOutputWriting):
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

    def write_result(self, result: object) -> None:
        stream = self._stream_factory()
        rendered = (
            result
            if isinstance(result, str)
            else self._serializer.serialize(result, indent=2)
        )
        stream.write(f"{rendered}\n")
        stream.flush()
