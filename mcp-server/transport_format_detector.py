"""
solid-name: TransportFormatDetector
solid-category: service
solid-description: Selects the reader/writer pair matching a transport's wire format, based on the
first byte received — '{' means newline-delimited JSON, otherwise Content-Length framing.
"""

from content_length_reader import ContentLengthReader
from content_length_writer import ContentLengthWriter
from jsonlines_reader import JsonlinesReader
from jsonlines_writer import JsonlinesWriter
from message_reading import MessageReading
from message_writing import MessageWriting
from transport_format_detecting import TransportFormatDetecting

_JSONLINES_MARKER = b"{"


class TransportFormatDetector(TransportFormatDetecting):

    def detect_reader(self, first_byte: bytes) -> MessageReading:
        return JsonlinesReader() if first_byte == _JSONLINES_MARKER else ContentLengthReader()

    def detect_writer(self, first_byte: bytes) -> MessageWriting:
        return JsonlinesWriter() if first_byte == _JSONLINES_MARKER else ContentLengthWriter()
