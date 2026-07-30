"""
solid-name: OutgoingMessageFactorying
solid-category: abstraction
solid-description: Contract for creating OutgoingMessageWriting instances for the transport format.
"""

from typing import Protocol

from outgoing_message_writing import OutgoingMessageWriting
from stdout_sink import StdoutSink
from transport_format_detecting import TransportFormatDetecting


class OutgoingMessageFactorying(Protocol):
    def create(
        self, stdout: StdoutSink, format_detector: TransportFormatDetecting, first_byte: bytes
    ) -> OutgoingMessageWriting: ...
