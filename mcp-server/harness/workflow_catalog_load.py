"""State shared by workflow-ID lookups during one flow-definition load."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from harness.workflow_catalog import WorkflowCatalog


"""
solid-name: WorkflowCatalogLoad
solid-category: model
solid-spec: [SPEC-035]
solid-description: Represents workflow catalog lookup state scoped to one flow-definition load.
"""
@dataclass
class WorkflowCatalogLoad:
    search_roots: list[Path]
    catalog: Optional[WorkflowCatalog] = None
