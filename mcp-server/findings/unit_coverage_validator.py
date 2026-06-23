"""
solid-name: UnitCoverageValidator
solid-category: service
solid-description: Validates that SOLID principle submissions cover all code units.
"""

from __future__ import annotations

from typing import Optional, Protocol


_SOLID_PRINCIPLES = frozenset({"srp", "ocp", "lsp", "isp", "dry"})


def load_applies_to(refs_root) -> dict:
    """Load applies_to constraints from each principle's rule.md frontmatter.

    Returns a dict mapping lowercase principle name → list of unit_kinds, for every
    principle that declares an applies_to field. Principles without the field are absent
    from the result (i.e. they apply to all unit kinds).
    """
    from pathlib import Path as _Path
    result: dict = {}
    principles_root = _Path(refs_root) / "principles"
    if not principles_root.is_dir():
        return result
    for rule_md in principles_root.glob("*/rule.md"):
        try:
            content = rule_md.read_text(encoding="utf-8")
            if not content.startswith("---"):
                continue
            end = content.find("---", 3)
            if end == -1:
                continue
            fm_text = content[3:end]
            applies_to = _parse_applies_to(fm_text, rule_md.parent.name)
            if applies_to is not None:
                result[rule_md.parent.name.lower()] = applies_to
        except Exception:
            continue
    return result


def _parse_applies_to(frontmatter_text: str, principle_name: str) -> list:
    """Extract the applies_to list from raw YAML frontmatter text, or None if absent."""
    in_applies = False
    items: list = []
    for line in frontmatter_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("applies_to:"):
            value = stripped[len("applies_to:"):].strip()
            if value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                return [v.strip() for v in inner.split(",")] if inner else []
            in_applies = True
            continue
        if in_applies:
            if stripped.startswith("- "):
                items.append(stripped[2:].strip())
            elif stripped and not stripped.startswith("#"):
                break
    return items if items else None


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


def _unit_kinds_in_submissions(submissions: dict) -> set:
    """Collect every unit_kind submitted across all principles."""
    kinds: set = set()
    for payload in submissions.values():
        if not isinstance(payload, dict):
            continue
        for f in payload.get("files", []):
            if not isinstance(f, dict):
                continue
            for unit in f.get("units", []):
                if isinstance(unit, dict):
                    k = unit.get("unit_kind", "")
                    if k:
                        kinds.add(k)
    return kinds


class UnitCoverageValidator(UnitCoverageValidating):
    """Rejects submissions where SOLID principles silently skip unit analysis.

    Primary: uses expected_units from an injected HookContextLoading implementation
    (extracted from source content before the LLM ran) — catches even the case where
    ALL principles skip on a non-empty file.
    Fallback: cross-principle comparison.

    applies_to: optional dict mapping principle name (lowercase) to a list of unit_kinds
    the principle governs. When provided, a principle with empty units is accepted if none
    of the submitted unit_kinds appear in its applies_to list — meaning the file has no
    units this principle governs.

    Conditional principles (swiftui, testing, structured-concurrency, code-smells,
    ui-test, xctest) are excluded — they legitimately have empty units.
    """

    def __init__(
        self,
        context_loader: Optional[HookContextLoading] = None,
        applies_to: Optional[dict] = None,
    ) -> None:
        self._context_loader = context_loader
        self._applies_to: dict = applies_to or {}

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
        skipped = self._find_skipped(submissions)
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
        skipped = self._find_skipped(submissions)
        if not skipped:
            return None
        return self._rejection(skipped, sorted(known_units), ", ".join(sorted(known_units)))

    def _find_skipped(self, submissions: dict) -> list:
        """Return SOLID principles that submitted empty units and are not exempt."""
        return [
            label for label, payload in submissions.items()
            if label.lower() in _SOLID_PRINCIPLES
            and _extract_unit_names(payload) == []
            and not self._exempt_empty(label, submissions)
        ]

    def _exempt_empty(self, label: str, submissions: dict) -> bool:
        """Return True if an empty submission is valid given applies_to constraints.

        A principle is exempt when it declares applies_to and none of the submitted
        unit_kinds match its constraint — the file has no units this principle governs.
        """
        constraint = self._applies_to.get(label.lower())
        if not constraint:
            return False
        submitted_kinds = _unit_kinds_in_submissions(submissions)
        return not (submitted_kinds & set(constraint))

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