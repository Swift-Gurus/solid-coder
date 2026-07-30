"""
solid-name: StdioOutgoingMessages
solid-category: service
solid-description: Sends outgoing messages to a specified output sink.
"""

from message_writing import MessageWriting
from outgoing_message_writing import OutgoingMessageWriting
from stdout_sink import StdoutSink


class StdioOutgoingMessages(OutgoingMessageWriting):

    def __init__(self, stdout: StdoutSink, writer: MessageWriting) -> None:
        self._stdout = stdout
        self._writer = writer

    def write_message(self, msg: dict) -> None:
        self._writer.write(self._stdout, msg)