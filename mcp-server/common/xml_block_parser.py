#!/usr/bin/env python3
"""
solid-description: Parses named XML blocks from markdown rule content into structured data.
solid-category: utility
solid-tags: [utility, service]
"""

import re
from typing import Any

_TAG_WITH_ID = re.compile(
    r"<(detection|definition|severity-bands)\s+id=['\"]([^'\"]+)['\"][^>]*>(.*?)</\1>",
    re.DOTALL,
)
_EXCEPTIONS_TAG = re.compile(
    r"<exceptions[^>]*>(.*?)</exceptions>",
    re.DOTALL,
)


def parse(content: str) -> dict[str, Any]:
    """Parse named XML blocks from rule.md content.

    Accepts raw rule.md text (with or without YAML frontmatter). Returns a
    dict with four keys:
      "detection"      -> {metric_id: str}
      "definition"     -> {metric_id: str}
      "severity-bands" -> {metric_id: str}
      "exceptions"     -> str  (empty string when absent)

    Never raises. Returns empty collections for absent or malformed blocks.
    """
    result: dict[str, Any] = {
        "detection": {},
        "definition": {},
        "severity-bands": {},
        "exceptions": "",
    }

    for match in _TAG_WITH_ID.finditer(content):
        block_type = match.group(1)
        metric_id = match.group(2)
        inner = match.group(3).strip()
        result[block_type][metric_id] = inner

    exceptions_match = _EXCEPTIONS_TAG.search(content)
    if exceptions_match:
        result["exceptions"] = exceptions_match.group(1).strip()

    return result
