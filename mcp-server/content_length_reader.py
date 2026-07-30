"""
solid-name: ContentLengthReader
solid-category: service
solid-description: Reads a message from the input stream and returns the parsed content.
"""

import json
from typing import Optional

from message_reading import MessageReading
from stdin_source import StdinSource


class ContentLengthReader(MessageReading):

    def read(self, stdin: StdinSource, peeked: bytes) -> Optional[dict]:
        headers = {}
        first = peeked
        while True:
            if first:
                raw = first + stdin.readline()
                first = b""
            else:
                raw = stdin.readline()
            if not raw:
                return None
            line = raw.decode("utf-8").strip()
            if not line:
                break
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip().lower()] = value.strip()
        length = int(headers.get("content-length", 0))
        if length == 0:
            return None
        body = stdin.read(length)
        return json.loads(body.decode("utf-8"))