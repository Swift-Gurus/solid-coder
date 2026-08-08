"""Caches collision-checked catalogs used during flow loading."""

from __future__ import annotations

from pathlib import Path

from harness.workflow_catalog import WorkflowCatalog
from harness.workflow_catalog_building import WorkflowCatalogBuilding
from harness.workflow_source import WorkflowSource


"""
solid-name: WorkflowCatalogResolver
solid-category: service
solid-spec: [SPEC-035]
solid-description: Resolves workflow IDs through one cached catalog per search-root set.
"""
class WorkflowCatalogResolver:

    def __init__(self, builder: WorkflowCatalogBuilding) -> None:
        self._builder = builder
        self._catalogs: dict[tuple[str, ...], WorkflowCatalog] = {}

    def resolve(self, workflow_id: str, search_paths: list[str]) -> WorkflowSource | None:
        key = tuple(str(Path(path).resolve()) for path in search_paths)
        catalog = self._catalogs.get(key)
        if catalog is None:
            catalog = self._builder.build([Path(path) for path in key])
            self._catalogs[key] = catalog
        return catalog.find(workflow_id)
