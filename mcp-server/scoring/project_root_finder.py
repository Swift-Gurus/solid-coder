"""
solid-description: Locates the topmost project root directory for configuration discovery.
solid-category: service
solid-tags: [utility, service]
"""

from pathlib import Path
from typing import Optional, Protocol

from scoring.parent_chain import parent_chain

CONFIG_DIR        = ".solid-coder"       # config directory name — mirrors hooks/solid_coder_paths.py
CONFIG_TOML       = "config.toml"        # root marker: directory is the root iff this file exists
CONFIG_BASENAME   = "severity-bands.yml" # threshold overrides — mirrors SEVERITY_BANDS


class ProjectRootFinding(Protocol):
    def find(self, file_path: str) -> Optional[str]: ...


class ProjectRootFinder:
    """Walks up from file_path to find the topmost ancestor that contains .solid-coder/config.toml.

    config.toml is the root marker — a .solid-coder/ directory without it is
    not treated as a project root. This prevents ~/.solid-coder/ (Claude Code
    config) and bare log/output directories from triggering false detection.

    Returns the topmost such ancestor so ConfigPathCollector can cascade all
    intermediate severity-bands.yml files root→leaf, with leaf configs winning
    key-by-key.
    """

    def find(self, file_path: str) -> Optional[str]:
        found = None
        for current in parent_chain(Path(file_path).resolve().parent):
            if (current / CONFIG_DIR / CONFIG_TOML).is_file():
                found = str(current)
        return found
