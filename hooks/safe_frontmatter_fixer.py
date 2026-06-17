"""
solid-description: Safely invokes the frontmatter fixer and translates subprocess errors into gate block decisions.
solid-category: service
solid-tags: [hook]
"""

from typing import Optional

from gate_protocols import FrontmatterFixing, GateHandling


class SafeFrontmatterFixer:
    """Invokes the frontmatter fixer, handles errors, and returns the corrected content or None."""

    def __init__(self, fixer: FrontmatterFixing) -> None:
        self._fixer = fixer

    def apply(self, content: str, session_id: str, path: str, gate: GateHandling, file_name: str) -> Optional[str]:
        try:
            return self._fixer.fix(content, session_id, path)
        except Exception as exc:
            gate.log(f"BLOCK {file_name}: frontmatter subprocess error: {exc}")
            gate.block(
                f"[frontmatter] Gate subprocess failed — the write is blocked.\n\nError: {exc}\n\n"
                f"Stop and report this error to the user. Do not attempt to write the file again "
                f"until the subprocess issue is resolved."
            )
            return None
