"""
solid-name: JsonlinesReader
solid-category: service
solid-description: Reads a single message from an input stream.
"""

import json

from message_reading import MessageReading
from stdin_source import StdinSource


class JsonlinesReader(MessageReading):
    def read(self, stdin: StdinSource, peeked: bytes) -> dict | None:
        line = peeked + stdin.readline()
        if not line or line.strip() == b"":
            return None
        try:
            return json.loads(line.decode("utf-8").strip())
        except json.JSONDecodeError:
            return None
