"""Defines one apply_patch invocation observed in a Codex transcript."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


"""
solid-name: CodexApplyPatchCall
solid-category: value
solid-description: Carries the patch content and transcript source for one observed Codex apply_patch invocation.
"""
@dataclass(frozen=True)
class CodexApplyPatchCall:

    patch_content: str
    transcript_path: Path
