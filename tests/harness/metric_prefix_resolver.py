"""
solid-name: MetricPrefixResolver
solid-category: service
solid-spec: [SPEC-014]
solid-description: Extracts a principle's metric-ID prefix (e.g. "FM" for frontmatter, "CS" for
code-smells) from its rule.md bands section, rather than assuming it matches the folder name —
several principles (frontmatter, code-smells) have a folder name that differs from their
metric-ID prefix.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parent
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from interfaces import MetricPrefixResolving  # noqa: E402

_BAND_KEY_RE = re.compile(r"^\s+([A-Za-z]+)-\d+:", re.MULTILINE)


class MetricPrefixResolver(MetricPrefixResolving):
    """Reads rule.md's frontmatter `bands:` section and returns the shared metric-ID prefix."""

    def resolve(self, principle_folder: Path) -> str:
        rule_path = principle_folder / "rule.md"
        content = rule_path.read_text(encoding="utf-8")
        frontmatter_end = content.find("\n---", 3)
        frontmatter = content[:frontmatter_end] if frontmatter_end != -1 else content
        match = _BAND_KEY_RE.search(frontmatter)
        if not match:
            raise ValueError(f"No metric band (e.g. 'FM-1:') found in {rule_path}")
        return match.group(1)
