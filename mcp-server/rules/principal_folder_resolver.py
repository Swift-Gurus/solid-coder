#!/usr/bin/env python3
"""
solid-description: Resolves principle identifiers to their filesystem locations.
solid-category: utility
solid-tags: [utility, service]
"""

from pathlib import Path


def resolve(
    principle: str,
    refs_root: Path,
    _registry=None,
) -> Path:
    """Resolve a principle name to its absolute folder path.

    Uses PrincipleRegistry to search the full references tree so principles
    outside references/principles/ (e.g. references/coding/apple/SwiftUI)
    are found alongside core SOLID principles.

    Args:
        principle:  Case-insensitive principle identifier, e.g. 'srp', 'swiftui'.
        refs_root:  Root of the references directory.
        _registry:  Optional pre-built PrincipleRegistry (injectable for testing).

    Returns:
        Absolute Path to the matching principle folder.

    Raises:
        ValueError:        When no folder matches the given principle name.
        FileNotFoundError: When refs_root does not exist.
    """
    if not refs_root.is_dir():
        raise FileNotFoundError(f"References directory not found: {refs_root}")

    from rules.principle_registry import PrincipleRegistry
    registry = _registry if _registry is not None else PrincipleRegistry(refs_root)
    all_p = registry.all_principles()

    target = principle.strip().lower()
    for p in all_p:
        if p["name"].lower() == target:
            return Path(p["folder"]).resolve()

    available = ", ".join(sorted(p["name"] for p in all_p))
    raise ValueError(
        f'Unknown principle: "{principle}". Available: {available}'
    )
