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

    result["exceptions"] = _line_delimited_body(content, "exceptions")

    return result


def _line_delimited_body(content: str, tag: str) -> str:
    lines = content.splitlines()
    opening_index: int | None = None
    opening_prefix = f"<{tag}"
    closing = f"</{tag}>"
    for index, line in enumerate(lines):
        stripped = line.strip()
        if (
            stripped.startswith(opening_prefix)
            and stripped.endswith(">")
            and len(stripped) > len(opening_prefix)
            and stripped[len(opening_prefix)] in {" ", ">"}
        ):
            opening_index = index
            break
    if opening_index is None:
        return ""
    for index in range(opening_index + 1, len(lines)):
        if lines[index].strip() == closing:
            return "\n".join(lines[opening_index + 1:index]).strip()
    return ""
