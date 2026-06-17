"""
solid-description: Classifies whether a code edit is structural-only and cannot introduce SOLID violations.
solid-category: service
solid-tags: [hook, utility]
"""

import re
from typing import ClassVar


class EditClassifier:
    """Classifies whether an edit is structural-only (low-risk) or requires health checking."""

    _SOLID_BLOCK_RE: ClassVar = re.compile(
        r"^\s*/\*\*\s*\n(?:[ \t]+solid-[^\n]+\n)+[ \t]*\*/\s*\Z"
    )

    def is_low_risk(self, old: str, new: str) -> bool:
        return self.is_frontmatter_only(old, new) or self.is_reorder(old, new) or self.is_rename(old, new)

    def is_frontmatter_only(self, old: str, new: str) -> bool:
        return bool(self._SOLID_BLOCK_RE.match(old.strip())) and bool(self._SOLID_BLOCK_RE.match(new.strip()))

    def is_reorder(self, old: str, new: str) -> bool:
        return sorted(re.findall(r'\w+', old)) == sorted(re.findall(r'\w+', new))

    def is_rename(self, old: str, new: str) -> bool:
        skeleton = lambda s: re.sub(r'\b\w+\b', 'X', s)
        return skeleton(old) == skeleton(new)