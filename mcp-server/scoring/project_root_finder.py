"""
solid-description: Walks the directory tree upward from a file to locate the topmost project root for configuration discovery.
solid-category: service
solid-tags: [utility, service]
"""

from pathlib import Path
from typing import Optional, Protocol

from scoring.parent_chain import parent_chain

CONFIG_DIR = ".solid-coder"
CONFIG_BASENAME = "severity-bands.yml"


class ProjectRootFinding(Protocol):
    def find(self, file_path: str) -> Optional[str]: ...


class ProjectRootFinder:
    """Walks up from file_path to find the topmost .solid-coder/ directory (project root).

    Returns the topmost ancestor containing a .solid-coder/ directory so that
    ConfigPathCollector can cascade all intermediate severity-bands.yml files
    root→leaf, with leaf configs winning key-by-key.
    """

    def find(self, file_path: str) -> Optional[str]:
        found = None
        for current in parent_chain(Path(file_path).resolve().parent):
            if (current / CONFIG_DIR).is_dir():
                found = str(current)
        return found
