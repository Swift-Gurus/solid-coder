"""Coordinates loading of readable specification ancestry context."""

from spec_ancestry_retrieving import SpecAncestryRetrieving
from spec_context_rendering import SpecContextRendering


"""
solid-name: SpecContextLoader
solid-category: service
solid-description: Coordinates retrieval and rendering of specification ancestry context.
"""
class SpecContextLoader:
    def __init__(
        self,
        retriever: SpecAncestryRetrieving,
        renderer: SpecContextRendering,
    ) -> None:
        self._retriever = retriever
        self._renderer = renderer

    def load(self, **arguments) -> str:
        spec_number = arguments.get("spec")
        if not spec_number:
            raise ValueError("--spec is required")
        specs = self._retriever.retrieve(
            spec_number,
            arguments.get("blocked", False),
        )
        return self._renderer.render(spec_number, specs)
