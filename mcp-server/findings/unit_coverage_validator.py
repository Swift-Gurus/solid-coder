"""
solid-name: UnitCoverageValidator
solid-category: service
solid-description: Validates that SOLID principle submissions cover all code units.
"""

from __future__ import annotations

from typing import Optional, Protocol


_SOLID_PRINCIPLES = frozenset({"srp", "ocp", "lsp", "isp", "dry"})


class HookContextLoading(Protocol):
    def load(self) -> Optional[dict]: ...


class UnitCoverageValidating(Protocol):
    def validate(self, submissions: dict) -> Optional[dict]: ...


def _extract_unit_names(principle_payload: dict) -> Optional[list]:
    """Return submitted unit names, or None if the payload is structurally invalid.

    None  = malformed (let schema validator handle it; exclude from coverage check).
    []    = valid structure, no units submitted — the silent-skip signal.
    [...] = units were submitted.
    """
    files = principle_payload.get("files", [])
    if not isinstance(files, list):
        return None
    return [
        unit.get("unit_name", "?")
        for f in files
        if isinstance(f, dict)
        for unit in f.get("units", [])
        if isinstance(unit, dict) and unit.get("unit_name")
    ]


class UnitCoverageValidator(UnitCoverageValidating):
    """Rejects submissions where SOLID principles silently skip unit analysis.

    Primary: uses expected_units from an injected HookContextLoading implementation
    (extracted from source content before the LLM ran) — catches even the case where
    ALL principles skip on a non-empty file.
    Fallback: cross-principle comparison — if sibling SOLID principles reported units
    but one didn't, the skip is detected even without hook context (e.g. in tests).

    Conditional principles (swiftui, testing, structured-concurrency, code-smells,
    ui-test, xctest) are excluded — they legitimately have empty units when the file
    does not use those patterns.
    """

    def __init__(self, context_loader: Optional[HookContextLoading] = None) -> None:
        self._context_loader = context_loader

    def validate(self, submissions: dict) -> Optional[dict]:
        if self._context_loader is not None:
            ctx = self._context_loader.load()
            if ctx is not None:
                expected = ctx.get("expected_units")
                if isinstance(expected, list):
                    return self._validate_against_expected(submissions, expected)
        return self._validate_cross_principle(submissions)

    def _validate_against_expected(self, submissions: dict, expected: list) -> Optional[dict]:
        if not expected:
            return None
        skipped = [
            label for label, payload in submissions.items()
            if label.lower() in _SOLID_PRINCIPLES
            and _extract_unit_names(payload) == []
        ]
        if not skipped:
            return None
        return self._rejection(skipped, expected, ", ".join(expected))

    def _validate_cross_principle(self, submissions: dict) -> Optional[dict]:
        known_units: set[str] = set()
        for label, payload in submissions.items():
            if label.lower() in _SOLID_PRINCIPLES:
                names = _extract_unit_names(payload)
                if names:
                    known_units.update(names)
        if not known_units:
            return None
        skipped = [
            label for label, payload in submissions.items()
            if label.lower() in _SOLID_PRINCIPLES
            and _extract_unit_names(payload) == []
        ]
        if not skipped:
            return None
        return self._rejection(skipped, sorted(known_units), ", ".join(sorted(known_units)))

    def _rejection(self, skipped: list, expected_units: list, units_str: str) -> dict:
        return {
            "error": "incomplete_submission",
            "detail": (
                f"Principles {skipped} submitted no units for a file containing "
                f"[{units_str}]. Every active SOLID principle must analyze every code "
                f"unit — submitting empty units is detectable and causes an expensive "
                f"re-run. Re-submit with complete analysis for {skipped}."
            ),
            "principles_with_no_units": skipped,
            "expected_units": expected_units,
        }