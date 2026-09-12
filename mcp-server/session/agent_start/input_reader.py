"""Reads raw agent-start input from the process boundary."""

import sys
from typing import Protocol, TextIO


"""
solid-name: AgentStartInputReading
solid-category: abstraction
solid-description: Contract for reading raw agent-start hook input.
"""
class AgentStartInputReading(Protocol):
    def read(self) -> str: ...


"""
solid-name: StdinAgentStartInputReader
solid-category: boundary
solid-description: Reads agent-start hook input from standard input.
"""
class StdinAgentStartInputReader(AgentStartInputReading):

    def __init__(self, source: TextIO = sys.stdin) -> None:
        self._source = source

    def read(self) -> str:
        return self._source.read()
