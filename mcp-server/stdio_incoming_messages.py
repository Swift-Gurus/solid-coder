"""
solid-name: StdioIncomingMessages
solid-category: service
solid-description: Reads framed JSON-RPC messages with automatic wire format detection
"""

from incoming_message_reading import IncomingMessageReading
from stdin_source import StdinSource
from transport_format_detecting import TransportFormatDetecting


class StdioIncomingMessages(IncomingMessageReading):
    def __init__(
        self, stdin: StdinSource, format_detector: TransportFormatDetecting
    ) -> None:
        self._stdin = stdin
        self._format_detector = format_detector
        self._reader = None
        self.detected_first_byte: bytes | None = None

    def read_message(self) -> dict | None:
        if self._reader is None:
            first = self._stdin.read(1)
            if not first:
                return None
            self.detected_first_byte = first
            self._reader = self._format_detector.detect_reader(first)
            return self._reader.read(self._stdin, first)
        return self._reader.read(self._stdin, b"")
