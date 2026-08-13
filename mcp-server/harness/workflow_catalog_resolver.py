"""Scopes collision-checked catalogs to individual flow-definition loads."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Iterator, Optional

from harness.workflow_catalog_building import WorkflowCatalogBuilding
from harness.workflow_catalog_load import WorkflowCatalogLoad
from harness.workflow_source import WorkflowSource


"""
solid-name: WorkflowCatalogResolver
solid-category: service
solid-spec: [SPEC-035]
solid-description: Resolves workflow IDs through one collision-checked catalog per flow-definition load.
"""
class WorkflowCatalogResolver:

    def __init__(self, builder: WorkflowCatalogBuilding) -> None:
        self._builder = builder
        self._active_load: ContextVar[Optional[WorkflowCatalogLoad]] = ContextVar(
            "workflow_catalog_load",
            default=None,
        )

    @contextmanager
    def scope(self, search_paths: list[str]) -> Iterator[None]:
        token = self._active_load.set(
            WorkflowCatalogLoad(search_roots=[Path(path) for path in search_paths])
        )
        try:
            yield
        finally:
            self._active_load.reset(token)

    def resolve(self, workflow_id: str, search_paths: list[str]) -> WorkflowSource | None:
        active_load = self._active_load.get()
        if active_load is None:
            return self._builder.build([Path(path) for path in search_paths]).find(workflow_id)

        if active_load.catalog is None:
            active_load.catalog = self._builder.build(active_load.search_roots)
        return active_load.catalog.find(workflow_id)
