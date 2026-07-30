"""
solid-name: ContentLengthWriter
solid-category: service
solid-description: Serializes messages and writes them to an output sink.
"""

from json_serializer import JsonSerializer, JsonSerializing
from message_writing import MessageWriting
from stdout_sink import StdoutSink


class ContentLengthWriter(MessageWriting):

    def __init__(self, serializer: JsonSerializing = None) -> None:
        self._serializer = serializer or JsonSerializer()

    def write(self, stdout: StdoutSink, msg: dict) -> None:
        body = self._serializer.serialize(msg).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n"
        stdout.write(header.encode("utf-8"))
        stdout.write(body)
        stdout.flush()
