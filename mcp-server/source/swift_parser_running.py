"""Defines execution of the Swift parser for source text."""

from typing import Protocol

from harness.script_execution_result import ScriptExecutionResult


"""
solid-name: SwiftParserRunning
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for executing one Swift parse and returning its structured process outcome.
"""
class SwiftParserRunning(Protocol):
    def run(self, source: str) -> ScriptExecutionResult: ...
