"""
solid-description: Retrieves fix strategy documentation for a given metric identifier.
solid-category: service
solid-tags: [utility, service]
"""

from typing import Protocol

from findings.fix_file_lookup import resolve_single_fix, list_available_fix_metric_ids
from rules.detection_rules_loader import AllPrinciplesProviding
from rules.load_reference import strip_frontmatter


class FixInstructionsLoading(Protocol):
    def load_fix_instructions(self, metric_id: str) -> str: ...


class FixInstructionsLoader:
    """Loads fix strategy text for a given metric ID."""

    def __init__(self, all_principles: AllPrinciplesProviding) -> None:
        self._all_principles = all_principles

    def load_fix_instructions(self, metric_id: str) -> str:
        norm = metric_id.strip().upper()
        all_p = self._all_principles.all_principles()
        result = resolve_single_fix(norm, all_p)
        if result is None:
            available = list_available_fix_metric_ids(all_p)
            return f"No fix file for metric '{norm}'. Available: {', '.join(available)}"
        content = strip_frontmatter(result["content"]).rstrip()
        return f"# {result['principle']} — {norm} Fix Strategy\n\n{content}\n"
