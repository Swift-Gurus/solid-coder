"""
solid-description: Filters principle submissions to retain only units whose kind matches the principle's applicable scope.
solid-category: service
solid-tags: [utility, service]
"""

# Maps principle agent name → frozenset of unit_kind values it applies to.
# Submissions for units with kinds outside the allowed set are dropped before
# scoring, preventing false SEVERE findings from wrong LLM submissions.
# Example: ISP applies only to protocols — class/struct/enum/function units
# submitted for ISP are discarded, never scored.
_ALLOWED_KINDS: dict = {
    "isp": frozenset({"protocol", "interface"}),
}


def filter_by_unit_kind(
    partial_output: dict,
    _allowed: dict = None,
) -> dict:
    """Remove units whose kind is outside the principle's applicable scope.

    Returns partial_output unchanged when the principle has no kind restriction.
    Returns a shallow copy with the units list filtered when a restriction exists.
    _allowed is injectable for testing; defaults to the module-level _ALLOWED_KINDS.
    """
    agent = partial_output.get("agent", "").lower()
    allowed = (_allowed if _allowed is not None else _ALLOWED_KINDS).get(agent)
    if allowed is None:
        return partial_output

    filtered_files = []
    for file_obj in partial_output.get("files", []):
        kept = [
            u for u in file_obj.get("units", [])
            if u.get("unit_kind", "").lower() in allowed
        ]
        filtered_files.append({**file_obj, "units": kept})

    return {**partial_output, "files": filtered_files}
