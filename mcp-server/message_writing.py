"""
solid-name: MessageWriting
solid-category: abstraction
solid-description: Contract for writing messages to an output sink.
"""

from typing import Protocol

from stdout_sink import StdoutSink


class MessageWriting(Protocol):
    def write(self, stdout: StdoutSink, msg: dict) -> None: ...