from hc_checker import HealthChecking
from health_check_outcome import HealthCheckOutcome
from health_violation import HealthViolation
from patch_review_context import PatchReviewContext

"""
solid-name: LegacyHealthOutcomeAdapter
solid-category: adapter
solid-spec: [SPEC-050, SPEC-057]
solid-description: Adapts legacy health review results to the shared gate outcome while preserving request context and rejecting absent results.
"""


class LegacyHealthOutcomeAdapter(HealthChecking[HealthCheckOutcome]):
    def __init__(self, checker: HealthChecking[list[HealthViolation] | None]) -> None:
        self._checker = checker

    def check(
        self,
        content: str,
        path: str,
        language: str,
        parent_session_id: str,
        cwd: str = "",
        patch_context: PatchReviewContext | None = None,
        principle_names: list[str] | None = None,
    ) -> HealthCheckOutcome:
        violations = self._checker.check(
            content,
            path,
            language,
            parent_session_id,
            patch_context=patch_context,
            principle_names=principle_names,
        )
        if violations is None:
            raise RuntimeError("Health checker returned no result")
        return HealthCheckOutcome(violations=violations)
