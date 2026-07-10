"""
solid-name: ActiveHealthCheckPointerStoring
solid-category: abstraction
solid-description: Contract for persisting and clearing which health check is currently active for a project.
"""

from pathlib import Path
from typing import Protocol


class ActiveHealthCheckPointerStoring(Protocol):

    def write(self, project_dir: Path, health_dir_name: str) -> None: ...

    def clear(self, project_dir: Path) -> None: ...
