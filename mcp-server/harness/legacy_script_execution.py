"""Defines execution of a legacy workflow script command array."""

from dataclasses import dataclass, field


"""
solid-name: LegacyScriptExecution
solid-category: model
solid-spec: [SPEC-027, SPEC-035]
solid-description: Represents a compatible legacy workflow script execution request.
"""
@dataclass(frozen=True)
class LegacyScriptExecution:
    arguments: list[str] = field(default_factory=list)

    def process_arguments(self) -> list[str]:
        return list(self.arguments)
