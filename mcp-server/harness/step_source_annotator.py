"""Annotates expanded steps with their declaring workflow file."""


"""
solid-name: StepSourceAnnotator
solid-category: service
solid-spec: [SPEC-035]
solid-description: Attaches immutable declaring-file provenance to each expanded workflow step.
"""
class StepSourceAnnotator:

    def annotate(self, steps: list[dict], source_path: str) -> list[dict]:
        return [dict(step, __source_file=source_path) for step in steps]
