"""Defines execution of a resolved workflow script file."""

from dataclasses import dataclass, field
from pathlib import Path


"""
solid-name: ScriptFileExecution
solid-category: model
solid-spec: [SPEC-035]
solid-description: Represents a resolved workflow script execution request.
"""
@dataclass(frozen=True)
class ScriptFileExecution:
    executor: str
    script_file: Path
    arguments: list[str] = field(default_factory=list)

    def process_arguments(self) -> list[str]:
        return [self.executor, str(self.script_file), *self.arguments]
