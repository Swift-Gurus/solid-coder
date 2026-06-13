"""
solid-description: Walks the directory chain from a file upward collecting .solid-coder.yml config files from the client project.
solid-category: service
solid-tags: [utility, service]
"""

from pathlib import Path
from typing import Optional, Protocol

CONFIG_FILENAME = ".solid-coder.yml"

try:
    import yaml as _yaml
    _YAML_AVAILABLE = True
except ImportError:
    _yaml = None  # type: ignore[assignment]
    _YAML_AVAILABLE = False


class DirectoryWalking(Protocol):
    def directories(self, file_path: str, root: Path) -> list: ...


class ConfigFileLoading(Protocol):
    def load(self, path: Path) -> Optional[dict]: ...


class ConfigCollecting(Protocol):
    def collect(self, file_path: str, project_root: Optional[str]) -> list: ...


class DirectoryWalker:
    """Produces the directory chain from root to file directory (root→leaf order)."""

    def directories(self, file_path: str, root: Path) -> list:
        p = Path(file_path).resolve()
        dirs: list = []
        current = p.parent
        while True:
            dirs.append(current)
            if current == root or current.parent == current:
                break
            current = current.parent
        return list(reversed(dirs))  # root → leaf


class YamlConfigFileLoader:
    """Loads and validates a single YAML config file from disk."""

    def load(self, path: Path) -> Optional[dict]:
        if not _YAML_AVAILABLE or not path.exists():
            return None
        try:
            result = _yaml.safe_load(path.read_text(encoding="utf-8"))
            return result if isinstance(result, dict) else None
        except Exception:
            return None


class ConfigPathCollector:
    """Facade: walks directories and loads .solid-coder.yml files (root→leaf order)."""

    def __init__(self, walker: DirectoryWalking, loader: ConfigFileLoading) -> None:
        self._walker = walker
        self._loader = loader

    def collect(self, file_path: str, project_root: Optional[str] = None) -> list:
        root = Path(project_root).resolve() if project_root else Path(file_path).resolve().parent
        configs = []
        for d in self._walker.directories(file_path, root):
            cfg = self._loader.load(d / CONFIG_FILENAME)
            if cfg:
                configs.append(cfg)
        return configs
