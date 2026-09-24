"""Qualifies included workflow steps under an alias."""

from harness.metric_scoring_source_qualifying import (
    MetricScoringSourceQualifying,
)


"""
solid-name: StepQualifier
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Prefixes an included step ID and its local step or group dependencies with one alias.
"""
class StepQualifier:
    def __init__(
        self,
        metric_source_qualifier: MetricScoringSourceQualifying,
    ) -> None:
        self._metric_source_qualifier = metric_source_qualifier

    def qualify(
        self,
        step: dict,
        alias: str,
        local_dependency_ids: set[str],
    ) -> dict:
        qualified = dict(step)
        qualified["id"] = f"{alias}.{step['id']}"
        qualified["depends_on"] = [
            f"{alias}.{dependency}"
            if dependency in local_dependency_ids
            else dependency
            for dependency in (step.get("depends_on") or [])
        ]
        scoring = step.get("scoring")
        if scoring is not None:
            qualified["scoring"] = self._metric_source_qualifier.qualify(
                scoring,
                alias,
                local_dependency_ids,
            )
        return qualified
