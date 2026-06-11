"""
solid-description: Processes fix submissions for violations and validates completeness.
solid-category: service
solid-tags: [utility, service]
"""

from typing import Any, Protocol

from findings.fix_persister import FixPersisting
from findings.fix_completeness_validator import FixCompletenessValidating


class FixSubmitting(Protocol):
    def submit_fix(self, output_dir: str, fixes: list) -> dict: ...


class FixSubmitter:
    """Facade: delegates persistence to FixPersisting and validation to FixCompletenessValidating."""

    def __init__(self, persister: FixPersisting, completeness: FixCompletenessValidating) -> None:
        self._persister = persister
        self._completeness = completeness

    def submit_fix(self, output_dir: str, fixes: list) -> dict[str, Any]:
        if not isinstance(fixes, list):
            return {"error": "'fixes' must be a list of {rule_id, file_path, unit_name, suggested_fix} objects"}

        persist_error = self._persister.persist(output_dir, fixes)
        if persist_error:
            return persist_error

        fixes_by_key = self._persister.load_all(output_dir)
        completeness_error = self._completeness.validate_completeness(output_dir, set(fixes_by_key))
        if completeness_error:
            return completeness_error

        return {"complete": True, "violations_with_fixes": self._completeness.violations_with_fixes(output_dir, fixes_by_key)}
