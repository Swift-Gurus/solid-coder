#!/usr/bin/env python3
"""
solid-description: Reads a single configuration value by section and key for use in shell scripts, returning a default when the value is absent.
solid-category: utility

Usage: python3 config_get.py <section> <key> [default]

Exits 0 and prints the value (or default) in all cases — never raises.
Falls back to the default when the file is missing, the key is absent,
or no TOML parser is available.
"""

import sys
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parents[1] / "hooks"
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from hook_utils import PLUGIN_ROOT, load_toml

_CONFIG = PLUGIN_ROOT / ".claude" / "solid-coder-local.toml"


def main() -> None:
    args = sys.argv[1:]
    if len(args) < 2:
        sys.exit("usage: config_get.py <section> <key> [default]")
    section, key = args[0], args[1]
    default = args[2] if len(args) > 2 else ""
    data = load_toml(_CONFIG) if _CONFIG.exists() else {}
    print(data.get(section, {}).get(key, default))


if __name__ == "__main__":
    main()
