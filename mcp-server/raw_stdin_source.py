"""
solid-name: RawStdinSource
solid-category: service
solid-description: Reads raw bytes from standard input.
"""

import sys

from stdin_source import StdinSource


class RawStdinSource(StdinSource):

    def read(self, n: int) -> bytes:
        return sys.stdin.buffer.read(n)

    def readline(self) -> bytes:
        return sys.stdin.buffer.readline()