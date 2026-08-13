"""Collects declaring-file provenance from resolved workflow steps."""


"""
solid-name: StepSourceCollector
solid-category: service
solid-spec: [SPEC-035]
solid-description: Collects unique declaring-file sources from resolved workflow steps while preserving selection order.
"""
class StepSourceCollector:
    def collect(self, steps: list[dict], existing_sources: list[str]) -> list[str]:
        sources = list(existing_sources)
        for step in steps:
            source = step.get("__source_file")
            if source is not None and source not in sources:
                sources.append(source)
        return sources
