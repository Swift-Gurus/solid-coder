"""Defines execution of an inline workflow command."""

from dataclasses import dataclass


"""
solid-name: InlineCommandExecution
solid-category: model
solid-spec: [SPEC-035]
solid-description: Represents an inline workflow command execution request.
"""
@dataclass(frozen=True)
class InlineCommandExecution:
    executor: str
    command: str

    def process_arguments(self) -> list[str]:
        return [self.executor, "-lc", self.command]
