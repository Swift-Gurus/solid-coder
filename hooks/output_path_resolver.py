"""
solid-description: Resolves a unique output directory for each gate invocation.
solid-category: service
solid-tags: [hook, utility]
"""

from typing import Callable, Optional, Protocol

from hook_utils import solid_coder_project_dir


class OutputPathResolving(Protocol):
    """Resolves a unique output directory for a single gate invocation."""

    def resolve(self, session_id: str) -> str: ...


class SessionOutputPathResolver:
    """Fallback resolver: uses the legacy gate/<session_id>/ path.

    Boundary adapter — wraps solid_coder_project_dir (plugin utility, not developer-owned).
    Inject project_dir_fn for testing.
    """

    def __init__(self, project_dir_fn: Optional[Callable] = None) -> None:
        self._project_dir_fn: Callable = project_dir_fn or solid_coder_project_dir

    def resolve(self, session_id: str) -> str:
        return str(self._project_dir_fn() / "gate" / session_id)
