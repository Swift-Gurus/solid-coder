"""
solid-description: Filters evaluation results to exclude principles from code constructs outside their applicable scope.
solid-category: service
solid-tags: [utility, service]
"""

# Maps principle name (as it appears in metrics keys) → frozenset of unit_kind values it applies to.
# Units with kinds outside the allowed set are dropped before scoring, preventing false SEVERE
# findings from wrong LLM submissions.
# Example: ISP applies only to protocols — class/struct/enum/function units are discarded.
_ALLOWED_KINDS: dict = {
    "ISP": frozenset({"protocol", "interface"}),
}


def filter_by_unit_kind(
    partial_output: dict,
    _allowed: dict = None,
) -> dict:
    """Remove units whose kind is outside the applicable scope for principles in their metrics.

    For each unit, checks whether any principle key in metrics has a kind restriction.
    If the unit's kind is not in the allowed set for that principle, the principle key
    is removed from the unit's metrics before scoring.

    Returns partial_output unchanged when no principle has kind restrictions.
    _allowed is injectable for testing; defaults to the module-level _ALLOWED_KINDS.
    """
    allowed_map = _allowed if _allowed is not None else _ALLOWED_KINDS
    if not allowed_map:
        return partial_output

    filtered_files = []
    changed = False
    for file_obj in partial_output.get("files", []):
        filtered_units = []
        for unit in file_obj.get("units", []):
            unit_kind = unit.get("unit_kind", "").lower()
            metrics = unit.get("metrics", {})
            filtered_metrics = {
                principle: m
                for principle, m in metrics.items()
                if principle not in allowed_map or unit_kind in allowed_map[principle]
            }
            if filtered_metrics != metrics:
                changed = True
                unit = {**unit, "metrics": filtered_metrics}
            filtered_units.append(unit)
        filtered_files.append({**file_obj, "units": filtered_units})

    if not changed:
        return partial_output
    return {**partial_output, "files": filtered_files}
