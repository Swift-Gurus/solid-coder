"""
solid-name: RawStdoutSink
solid-category: service
solid-description: Writes raw bytes to standard output.
"""

import sys

from stdout_sink import StdoutSink


class RawStdoutSink(StdoutSink):

    def write(self, data: bytes) -> None:
        sys.stdout.buffer.write(data)

    def flush(self) -> None:
        sys.stdout.buffer.flush()
