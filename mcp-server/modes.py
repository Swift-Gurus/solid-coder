"""Single source of truth for pipeline mode → load configuration.

Each pipeline skill declares a `mode` instead of a `profile + exclude` pair.
This module maps mode → (profile, exclude sections, aggregation strategy).

Imported by:
  - server.py           (load_rules_for_mode tool)
  - gateway.py          (CLI alias)
  - scripts/token-cost-by-mode.py (doc generator)

Change a mode's load shape in ONE place.
"""

# Sections a principle folder can contribute:
#   rule          — rule.md
#   instructions  — review/instructions.md OR fix/instructions.md (depends on profile)
#   code_rules    — code/instructions.md (code profile only)
#   examples      — Examples/*.swift
#   patterns      — files listed in rule.md frontmatter (required_patterns)


MODES = {
    "code": {
        "profile": "code",
        "exclude": ["rule", "instructions", "examples", "patterns"],
        "aggregation": "all",
        "description": "`/code` and `/implement` coding phase — write SOLID-compliant code",
        "loads": ["code_rules"],
    },
    "review": {
        "profile": "review",
        "exclude": ["patterns"],
        "aggregation": "per-principle",
        "description": "`apply-principle-review` subagent — detect violations against a single principle",
        "loads": ["rule", "instructions", "examples"],
    },
    "planner": {
        "profile": "code",
        "exclude": ["examples", "instructions", "code_rules", "patterns"],
        "aggregation": "all",
        "description": "`plan` — architecture decomposition from a feature spec",
        "loads": ["rule"],
    },
    "synth-impl": {
        "profile": "code",
        "exclude": ["examples", "instructions", "patterns"],
        "aggregation": "all",
        "description": "`synthesize-implementation` — reconcile arch + validation into an implementation plan",
        "loads": ["rule", "code_rules"],
    },
    "synth-fixes": {
        "profile": "code",
        "exclude": ["examples", "patterns"],
        "aggregation": "all",
        "description": "`synthesize-fixes` — holistic fix planner (loop loads all principles into one context)",
        "loads": ["rule", "code_rules", "instructions"],
    },
}


# Human-readable labels for the "Loads" column in the generated doc.
SECTION_LABELS = {
    "rule": "rule.md",
    "code_rules": "code/instructions.md",
    "instructions": "fix or review/instructions.md",
    "examples": "Examples/",
    "patterns": "required_patterns",
}


def resolve(mode: str) -> dict:
    """Return the load config for a mode name. Raises KeyError if unknown."""
    if mode not in MODES:
        raise KeyError(f"Unknown mode '{mode}'. Valid: {', '.join(MODES)}")
    return MODES[mode]
