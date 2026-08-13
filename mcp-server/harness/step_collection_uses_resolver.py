"""Resolves reusable fragments across workflow step collections."""

from harness.uses_resolving import UsesResolving


"""
solid-name: StepCollectionUsesResolver
solid-category: service
solid-spec: [SPEC-030, SPEC-035]
solid-description: Resolves reusable fragments for every step in a workflow collection.
"""
class StepCollectionUsesResolver:
    def __init__(self, step_resolver: UsesResolving) -> None:
        self._step_resolver = step_resolver

    def resolve(
        self,
        steps: list[dict],
        flow_path: str,
        search_paths: list[str],
    ) -> list[dict]:
        return [
            self._step_resolver.resolve(step, flow_path, search_paths)
            for step in steps
        ]
