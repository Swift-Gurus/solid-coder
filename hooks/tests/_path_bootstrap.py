"""
solid-description: Ensures specified directories are available for module imports in the current process.
solid-category: unit-test
"""

import sys
from pathlib import Path


def ensure_on_path(*dirs: Path) -> None:
    for d in dirs:
        s = str(d)
        if s not in sys.path:
            sys.path.insert(0, s)
