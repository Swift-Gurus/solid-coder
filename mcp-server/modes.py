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
#   rule          — rule.md (always loaded; can't be excluded)
#   instructions  — review/instructions.md OR fix/instructions.md (depends on profile)
#   code_rules    — code/instructions.md (code profile only)
#   examples      — Examples/*.swift
#   patterns      — files listed in rule.md frontmatter (required_patterns)

# Rule-content stripping — review-only content (detection checklists, scoring,
# severity bands) is removed from rule.md for non-review modes. The coder only
# cares about the rule statement + definition + constraints — not how to detect
# or score violations.
STRIP_H2_SECTIONS = [
    "Quantitative Metrics Summary",  # severity bands + thresholds table
]
STRIP_H3_SECTIONS = [
    "Severity Bands",          # review-only severity bands per rule
    "Severity Bands:",         # colon variant
]
STRIP_BOLD_SUBSECTIONS = [
    "Detection",       # "how to find violations" checklists
    "Count",           # counting instructions
    "Analysis",
    "Score",
    "Scoring",
    "Scope",
    "Result",          # empty result tables for reviewers
    "Classify matches",
    "Classify each as",
    "Check injection style",
    "Not in scope",
]


MODES = {
    "code": {
        "profile": "code",
        "exclude": ["instructions", "examples"],
        "aggregation": "all",          # loads all active principles into one context
        "description": "`/code` and `/implement` coding phase — write SOLID-compliant code",
        "loads": ["rule", "code_rules", "patterns"],
        "strip_review_content": True,
    },
    "review": {
        "profile": "review",
        "exclude": [],
        "aggregation": "per-principle",  # each apply-principle-review subagent loads one principle
        "description": "`apply-principle-review` subagent — detect violations against a single principle",
        "loads": ["rule", "instructions", "examples", "patterns"],
        "strip_review_content": False,
    },
    "planner": {
        "profile": "code",
        "exclude": ["examples", "instructions"],
        "aggregation": "all",
        "description": "`plan` — architecture decomposition from a feature spec",
        "loads": ["rule", "code_rules", "patterns"],
        "strip_review_content": True,
    },
    "synth-impl": {
        "profile": "code",
        "exclude": ["examples", "instructions"],
        "aggregation": "all",
        "description": "`synthesize-implementation` — reconcile arch + validation into an implementation plan",
        "loads": ["rule", "code_rules", "patterns"],
        "strip_review_content": True,
    },
    "synth-fixes": {
        "profile": "code",
        "exclude": ["examples"],
        "aggregation": "all",
        "description": "`synthesize-fixes` — holistic fix planner (loop loads all principles into one context)",
        "loads": ["rule", "code_rules", "instructions", "patterns"],
        "strip_review_content": True,
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