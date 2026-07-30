"""
solid-name: StdioOutgoingMessageFactory
solid-category: service
solid-description: Creates message writers for the transport format.
"""

from outgoing_message_factory import OutgoingMessageFactorying
from outgoing_message_writing import OutgoingMessageWriting
from stdio_outgoing_messages import StdioOutgoingMessages
from stdout_sink import StdoutSink
from transport_format_detecting import TransportFormatDetecting


class StdioOutgoingMessageFactory(OutgoingMessageFactorying):

    def create(
        self, stdout: StdoutSink, format_detector: TransportFormatDetecting, first_byte: bytes
    ) -> OutgoingMessageWriting:
        writer = format_detector.detect_writer(first_byte)
        return StdioOutgoingMessages(stdout, writer)
