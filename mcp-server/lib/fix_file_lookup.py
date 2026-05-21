#!/usr/bin/env python3
"""
solid-description: Resolves fix-guidance content for metric IDs from the available set of principle definitions.
solid-category: utility
solid-tags: [utility, service]
"""

from pathlib import Path
from typing import Optional


def find_fix_file(metric_id: str, all_principles: list) -> tuple:
    """Search all principle folders for fix/{metric_id}.md.

    Args:
        metric_id:      Normalized metric ID, e.g. 'OCP-1'.
        all_principles: List of principle entry dicts (each has a 'folder' key).

    Returns:
        (principle_entry, Path) if found, (None, None) if not found.
    """
    for p in all_principles:
        fp = Path(p["folder"]) / "fix" / f"{metric_id}.md"
        if fp.is_file():
            return p, fp
    return None, None


def list_available_fix_metric_ids(all_principles: list) -> list[str]:
    """Return sorted list of all available fix metric ID stems across all principles.

    Args:
        all_principles: List of principle entry dicts (each has a 'folder' key).

    Returns:
        Sorted list of metric ID strings (e.g. ['DRY-1', 'OCP-1', 'SRP-2']).
    """
    return sorted(
        f.stem
        for p in all_principles
        for f in (Path(p["folder"]) / "fix").glob("*.md")
        if (Path(p["folder"]) / "fix").is_dir() and f.stem != "instructions"
    )


def resolve_single_fix(metric_id: str, all_principles: list) -> Optional[dict]:
    """Find and read the fix content for a metric ID.

    Args:
        metric_id:      Normalized metric ID, e.g. 'OCP-1'.
        all_principles: List of principle entry dicts.

    Returns:
        Dict with principle, metric_id, content keys if found; None if not found.
    """
    entry, fix_path = find_fix_file(metric_id, all_principles)
    if fix_path is None:
        return None
    return {
        "principle": entry["name"].upper(),
        "metric_id": metric_id,
        "content": fix_path.read_text(encoding="utf-8"),
    }
