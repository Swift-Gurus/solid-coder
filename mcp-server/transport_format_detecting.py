"""
solid-name: TransportFormatDetecting
solid-category: abstraction
solid-description: Contract for selecting message reader and writer implementations for a detected transport format.
"""

from typing import Protocol

from message_reading import MessageReading
from message_writing import MessageWriting


class TransportFormatDetecting(Protocol):
    def detect_reader(self, first_byte: bytes) -> MessageReading: ...

    def detect_writer(self, first_byte: bytes) -> MessageWriting: ...