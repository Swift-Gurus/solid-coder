"""Associates a write tool with its content simulation capability."""

from dataclasses import dataclass

from content_simulating import ContentSimulating


"""
solid-name: ContentSimulatorRegistration
solid-category: model
solid-description: Associates a supported write-operation identity with its prospective-content simulation capability.
solid-tags: [hook]
"""
@dataclass(frozen=True)
class ContentSimulatorRegistration:
    tool_name: str
    simulator: ContentSimulating
