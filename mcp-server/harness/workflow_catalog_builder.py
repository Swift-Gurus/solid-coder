"""Coordinates discovery and indexing into one immutable catalog."""

from __future__ import annotations

from pathlib import Path

from harness.workflow_catalog import WorkflowCatalog
from harness.workflow_catalog_building import WorkflowCatalogBuilding
from harness.workflow_source_discovering import WorkflowSourceDiscovering
from harness.workflow_source_indexing import WorkflowSourceIndexing


"""
solid-name: WorkflowCatalogBuilder
solid-category: service
solid-spec: [SPEC-035]
solid-description: Coordinates workflow source discovery and collision-checked catalog indexing.
"""
class WorkflowCatalogBuilder(WorkflowCatalogBuilding):

    def __init__(
        self,
        discoverer: WorkflowSourceDiscovering,
        indexer: WorkflowSourceIndexing,
    ) -> None:
        self._discoverer = discoverer
        self._indexer = indexer

    def build(self, roots: list[Path]) -> WorkflowCatalog:
        sources = [source for root in roots for source in self._discoverer.discover(root)]
        return WorkflowCatalog(sources=self._indexer.index(sources))
