#!/usr/bin/env python3
"""
solid-description: Retrieves configuration values by section and key with safe default fallbacks.
solid-category: utility

Usage: python3 config_get.py <section> <key> [default]

Exits 0 and prints the value (or default) in all cases — never raises.
Falls back to the default when the file is missing, the key is absent,
or no TOML parser is available.
"""

import sys
from pathlib import Path
from typing import Callable

_HOOKS_DIR = Path(__file__).resolve().parents[1] / "hooks"
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))
import sys as _sys
from pathlib import Path as _Path
_PROJECT_ROOT = _Path(__file__).resolve().parents[1]
_sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server/health/config"))

from hc_config_core import read_section  # noqa: E402


class ConfigReader:
    """Looks up a single key from a merged config section with a safe default."""

    def __init__(self, section_reader: Callable[[str], dict]) -> None:
        self._read = section_reader

    def get(self, section: str, key: str, default: str = "") -> str:
        return str(self._read(section).get(key, default))


def main() -> None:
    args = sys.argv[1:]
    if len(args) < 2:
        sys.exit("usage: config_get.py <section> <key> [default]")
    section, key = args[0], args[1]
    default = args[2] if len(args) > 2 else ""
    print(ConfigReader(read_section).get(section, key, default))


if __name__ == "__main__":
    main()
