"""Qualifies included workflow steps under an alias."""


"""
solid-name: StepQualifier
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Prefixes an included step ID and its intra-group sibling dependencies with one alias.
"""
class StepQualifier:

    def qualify(self, step: dict, alias: str, sibling_ids: set[str]) -> dict:
        qualified = dict(step)
        qualified["id"] = f"{alias}.{step['id']}"
        qualified["depends_on"] = [
            f"{alias}.{dependency}" if dependency in sibling_ids else dependency
            for dependency in (step.get("depends_on") or [])
        ]
        return qualified
