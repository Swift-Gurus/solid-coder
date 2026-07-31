"""
solid-name: StderrLogger
solid-category: service
solid-description: Logs messages to an output stream.
solid-tags: [hook]
"""

import sys

from logging_protocol import Logging


class StderrLogger(Logging):
    def log(self, msg: str) -> None:
        sys.stderr.write(msg + "\n")