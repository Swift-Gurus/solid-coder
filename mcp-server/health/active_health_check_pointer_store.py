"""
solid-name: ActiveHealthCheckPointerStore
solid-category: service
solid-description: Maintains the active health check directory for a project.
"""

from pathlib import Path


class ActiveHealthCheckPointerStore:
    """Boundary adapter: persists the active-health-check pointer file on disk.

    Path.mkdir/write_text/unlink are stdlib-owned (not developer-owned, cannot
    be subclassed) — direct use here satisfies the OCP Boundary Adapter
    exception, same as SubprocessAdapter wrapping subprocess.run.
    """

    _POINTER_NAME = "active-health-check"

    def write(self, project_dir: Path, health_dir_name: str) -> None:
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / self._POINTER_NAME).write_text(health_dir_name, encoding="utf-8")

    def clear(self, project_dir: Path) -> None:
        (project_dir / self._POINTER_NAME).unlink(missing_ok=True)