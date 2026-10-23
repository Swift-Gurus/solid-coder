"""Defines parsed command-line arguments for the gateway."""

from dataclasses import dataclass

"""
solid-name: GatewayArguments
solid-category: model
solid-description: Carries one requested gateway tool name and its parsed arguments.
"""


@dataclass(frozen=True)
class GatewayArguments:
    tool_name: str | None
    values: dict
