"""Validates the stable namespace.name operation syntax."""

from harness.logical_operation_name_validating import (
    LogicalOperationNameValidating,
)


"""
solid-name: LogicalOperationNameValidator
solid-category: service
solid-spec: [SPEC-010, SPEC-040]
solid-description: Validates logical operation names independently of MCP transport naming.
"""
class LogicalOperationNameValidator(LogicalOperationNameValidating):
    def is_valid(self, name: str) -> bool:
        parts = name.split(".")
        return (
            len(parts) == 2
            and all(parts)
            and all(
                character.isalnum() or character in {"-", "_"}
                for part in parts
                for character in part
            )
        )
