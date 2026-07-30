"""
solid-name: JsonlinesWriter
solid-category: service
solid-description: Writes messages to a sink using a configurable formatter.
"""

from jsonlines_message_formatting import JsonlinesMessageFormatting
from jsonlines_message_formatter import JsonlinesMessageFormatter
from message_writing import MessageWriting
from stdout_sink import StdoutSink


class JsonlinesWriter(MessageWriting):

    def __init__(self, formatter: JsonlinesMessageFormatting = None) -> None:
        self._formatter = formatter or JsonlinesMessageFormatter()

    def write(self, stdout: StdoutSink, msg: dict) -> None:
        stdout.write(self._formatter.format(msg))
        stdout.flush()