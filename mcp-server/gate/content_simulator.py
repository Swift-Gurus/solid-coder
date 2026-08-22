"""
solid-description: Dispatches tool events to the appropriate per-tool content simulator.
solid-category: service
solid-tags: [hook]
"""

from content_simulating import ContentSimulating
from content_simulator_registration import ContentSimulatorRegistration
from simulated_write import SimulatedWrite


"""
solid-name: ContentSimulator
solid-description: Routes supported write operations through their prospective-content simulation policy.
solid-category: service
solid-tags: [hook]
"""
class ContentSimulator:
    """Facade: dispatches simulate() calls to the matching per-tool handler."""

    def __init__(self, registrations: list[ContentSimulatorRegistration]) -> None:
        self._registrations = registrations

    def simulate(self, tool_name: str, tool_input: dict) -> SimulatedWrite:
        registration = next(
            (
                candidate
                for candidate in self._registrations
                if candidate.tool_name == tool_name
            ),
            None,
        )
        if registration is None:
            return SimulatedWrite(
                content="",
                existing_content="",
                low_risk=True,
            )
        return registration.simulator.simulate(tool_name, tool_input)
