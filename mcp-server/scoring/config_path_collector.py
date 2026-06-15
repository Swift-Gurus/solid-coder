"""
solid-description: Collects configurations from the file system hierarchy.
solid-category: service
solid-tags: [utility, service]
"""

from pathlib import Path
from typing import Optional, Protocol

from scoring.project_root_finder import ProjectRootFinding, CONFIG_DIR, CONFIG_BASENAME
from scoring.directory_walker import DirectoryWalking
from scoring.yaml_config_file_loader import ConfigFileLoading


class ConfigCollecting(Protocol):
    def collect(self, file_path: str, project_root: Optional[str]) -> list: ...


class ConfigPathCollector:
    """Facade: walks directories and loads .solid-coder/severity-bands.yml files (root→leaf order)."""

    def __init__(
        self,
        walker: DirectoryWalking,
        loader: ConfigFileLoading,
        root_finder: ProjectRootFinding,
    ) -> None:
        self._walker = walker
        self._loader = loader
        self._root_finder = root_finder

    def collect(self, file_path: str, project_root: Optional[str] = None) -> list:
        detected = project_root or (self._root_finder.find(file_path) if file_path else None)
        root = Path(detected).resolve() if detected else Path(file_path).resolve().parent
        configs = []
        for d in self._walker.directories(file_path, root):
            cfg = self._loader.load(d / CONFIG_DIR / CONFIG_BASENAME)
            if cfg:
                configs.append(cfg)
        return configs
