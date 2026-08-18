"""Creates durable artifact directories for live integration sessions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from live_session_artifact_scope import LiveSessionArtifactScope


"""
solid-name: LiveSessionArtifactDirectoryCreator
solid-category: test-support
solid-description: Creates uniquely named backend-specific directories for durable live-session evidence.
"""
class LiveSessionArtifactDirectoryCreator:

    def create(
        self,
        project_root: Path,
        backend: str,
        scope: LiveSessionArtifactScope,
    ) -> Path:
        self._validate_component(scope.domain)
        self._validate_component(scope.scenario)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        artifact_directory = (
            project_root
            / ".solid-coder"
            / ".artifacts"
            / "test"
            / backend
            / "e2e"
            / scope.domain
            / scope.scenario
            / f"{timestamp}-{uuid.uuid4().hex[:8]}"
        )
        artifact_directory.mkdir(parents=True)
        return artifact_directory

    @staticmethod
    def _validate_component(component: str) -> None:
        if (
            not component
            or component in {".", ".."}
            or Path(component).name != component
        ):
            raise ValueError(
                "Live-session artifact scope components must be non-empty "
                "single directory names"
            )
