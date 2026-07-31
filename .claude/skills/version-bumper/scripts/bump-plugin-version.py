#!/usr/bin/env python3
"""Bump the solid-coder plugin version across all plugin.json manifests.

Usage:
    python3 bump-plugin-version.py [--part major|minor|patch] [--set X.Y.Z]

Reads the current version from every manifest, asserts they all agree (a
mismatch is treated as a real bug, not something to silently resolve), then
writes the new version back to each file, preserving existing formatting.

Exit codes:
    0 — success
    1 — error (manifest missing, versions disagree, invalid version string)
"""

import argparse
import json
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_MANIFEST_PATHS = [
    _REPO_ROOT / ".claude-plugin" / "plugin.json",
    _REPO_ROOT / ".codex-plugin" / "plugin.json",
]

_VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def _parse_version(raw: str) -> tuple:
    match = _VERSION_RE.match(raw)
    if not match:
        raise ValueError(f"Not a semver version: {raw!r}")
    return tuple(int(g) for g in match.groups())


def _bump(version: tuple, part: str) -> tuple:
    major, minor, patch = version
    if part == "major":
        return (major + 1, 0, 0)
    if part == "minor":
        return (major, minor + 1, 0)
    return (major, minor, patch + 1)


def _read_current_version(manifest_paths: list) -> str:
    versions = {}
    for path in manifest_paths:
        if not path.is_file():
            raise FileNotFoundError(f"Manifest not found: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        versions[str(path)] = data.get("version", "")

    distinct = set(versions.values())
    if len(distinct) != 1:
        detail = "\n".join(f"  {p}: {v!r}" for p, v in versions.items())
        raise ValueError(f"Manifests disagree on version, refusing to guess:\n{detail}")

    return distinct.pop()


def _write_version(manifest_paths: list, new_version: str) -> None:
    for path in manifest_paths:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
        old_version = data.get("version", "")
        updated = text.replace(
            f'"version": "{old_version}"',
            f'"version": "{new_version}"',
            1,
        )
        path.write_text(updated, encoding="utf-8")


def bump_versions(manifest_paths: list, part: str = "patch", set_version: str = None) -> tuple:
    """Bump every manifest's version. Returns (old_version, new_version)."""
    current = _read_current_version(manifest_paths)

    if set_version is not None:
        _parse_version(set_version)  # validate shape
        new_version = set_version
    else:
        new_version = ".".join(str(n) for n in _bump(_parse_version(current), part))

    _write_version(manifest_paths, new_version)
    return current, new_version


def main() -> None:
    parser = argparse.ArgumentParser(description="Bump the solid-coder plugin version.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--part", choices=["major", "minor", "patch"], default="patch")
    group.add_argument("--set", dest="set_version", help="Set an exact version, e.g. 2.0.0")
    args = parser.parse_args()

    try:
        old_version, new_version = bump_versions(_MANIFEST_PATHS, part=args.part, set_version=args.set_version)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"{old_version} -> {new_version}")


if __name__ == "__main__":
    main()
