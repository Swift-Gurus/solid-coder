#!/usr/bin/env python3
"""
solid-description: Retrieves a configuration value by section and key, returning a caller-supplied default when the value is absent or the configuration source is unavailable.
solid-category: utility

Usage: python3 config_get.py <section> <key> [default]

Exits 0 and prints the value (or default) in all cases — never raises.
Falls back to the default when the file is missing, the key is absent,
or no TOML parser is available.
"""

import sys
from pathlib import Path

_CONFIG = Path(__file__).resolve().parents[1] / ".claude" / "solid-coder-local.toml"


def _load(path: Path) -> dict:
    try:
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]
        with open(path, "rb") as f:
            return tomllib.load(f)
    except Exception:
        return {}


def main() -> None:
    args = sys.argv[1:]
    if len(args) < 2:
        sys.exit("usage: config_get.py <section> <key> [default]")
    section, key = args[0], args[1]
    default = args[2] if len(args) > 2 else ""
    data = _load(_CONFIG) if _CONFIG.exists() else {}
    print(data.get(section, {}).get(key, default))


if __name__ == "__main__":
    main()
