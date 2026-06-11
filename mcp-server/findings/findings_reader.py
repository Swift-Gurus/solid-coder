#!/usr/bin/env python3
"""
solid-description: Extracts a deduplicated, ordered list of metric IDs from a findings document.
solid-category: utility
solid-tags: [utility, service]
"""


def collect_metric_ids(raw: dict) -> list[str]:
    """Extract unique metric IDs from a findings JSON document.

    Supports both the by-file output structure:
      {"principles": [{"findings": [{"metric": "OCP-1"}]}]}
    and the flat findings structure:
      {"findings": [{"metric_id": "OCP-1"}]}

    Args:
        raw: Parsed findings JSON dict.

    Returns:
        Ordered list of unique uppercase metric ID strings (first-seen order).
    """
    metric_ids: list[str] = []
    seen: set[str] = set()

    for p in raw.get("principles", []):
        for f in p.get("findings", []):
            m = (f.get("metric") or f.get("metric_id") or "").strip().upper()
            if m and m not in seen:
                seen.add(m)
                metric_ids.append(m)

    for f in raw.get("findings", []):
        m = (f.get("metric_id") or f.get("metric") or "").strip().upper()
        if m and m not in seen:
            seen.add(m)
            metric_ids.append(m)

    return metric_ids
