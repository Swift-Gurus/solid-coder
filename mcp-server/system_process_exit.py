"""Terminates command-line processes through the system runtime."""

import sys

from process_exiting import ProcessExiting


"""
solid-name: SystemProcessExit
solid-category: boundary-adapter
solid-description: Terminates a command-line process with a requested status code.
"""
class SystemProcessExit(ProcessExiting):
    def exit(self, status: int) -> None:
        sys.exit(status)
