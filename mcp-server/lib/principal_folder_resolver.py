#!/usr/bin/env python3
"""
solid-description: Maps a principle identifier to the absolute path of its corresponding principle folder, raising an error when the identifier is unrecognised.
solid-category: utility
solid-tags: [utility, service]
"""

from pathlib import Path


def resolve(principle: str, refs_root: Path) -> Path:
    """Resolve a principle name to its absolute folder path.

    Args:
        principle: Case-insensitive principle identifier, e.g. 'srp', 'OCP', 'dry'.
        refs_root: Root of the references directory (parent of the principles/ folder).

    Returns:
        Absolute Path to the matching principle folder.

    Raises:
        ValueError: When no folder matches the given principle name.
        FileNotFoundError: When refs_root/principles/ does not exist.
    """
    principles_dir = refs_root / "principles"
    if not principles_dir.is_dir():
        raise FileNotFoundError(f"Principles directory not found: {principles_dir}")

    target = principle.strip().lower()
    candidates = [d for d in principles_dir.iterdir() if d.is_dir()]

    for folder in candidates:
        if folder.name.lower() == target:
            return folder.resolve()

    available = ", ".join(sorted(d.name for d in candidates))
    raise ValueError(
        f'Unknown principle: "{principle}". Available: {available}'
    )
