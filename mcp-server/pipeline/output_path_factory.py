"""
solid-description: Generates standardized output directory paths for solid-coder operations.
solid-category: service
"""

from __future__ import annotations

import os
import uuid as _uuid
from datetime import datetime, timezone
from pathlib import Path


class OutputPathFactory:
    """Generates standardized output directory paths for solid-coder operations."""

    def compute(self, operation: str, spec_number: str = "") -> dict:
        project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
        slug = str(Path(project_dir).resolve()).replace("/", "-")
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        if operation == "health":
            dir_name = f"health-{_uuid.uuid4()}"
        elif operation == "implement" and spec_number:
            dir_name = f"implement-{spec_number}-{ts}"
        else:
            dir_name = f"{operation}-{ts}"
        return {"output_root": str(Path.home() / ".solid-coder" / slug / dir_name)}
