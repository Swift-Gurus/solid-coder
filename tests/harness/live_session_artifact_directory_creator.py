"""Creates durable artifact directories for live integration sessions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path


"""
solid-name: LiveSessionArtifactDirectoryCreator
solid-category: test-support
solid-description: Creates uniquely named backend-specific directories for durable live-session evidence.
"""
class LiveSessionArtifactDirectoryCreator:

    def create(self, project_root: Path, backend: str) -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        artifact_directory = (
            project_root
            / ".solid-coder"
            / ".artifacts"
            / "test"
            / backend
            / "e2e"
            / "live-session"
            / f"{timestamp}-{uuid.uuid4().hex[:8]}"
        )
        artifact_directory.mkdir(parents=True)
        return artifact_directory
