"""Assembles the production workflow catalog resolver."""

from __future__ import annotations

from harness.package_workflow_source_discoverer import PackageWorkflowSourceDiscoverer
from harness.pydantic_model_decoder import PydanticModelDecoder
from harness.workflow_catalog_builder import WorkflowCatalogBuilder
from harness.workflow_catalog_resolver import WorkflowCatalogResolver
from harness.workflow_package_catalog_document import WorkflowPackageCatalogDocument
from harness.workflow_source_indexer import WorkflowSourceIndexer
from scoring.yaml_config_file_loader import YamlConfigFileLoader
from scoring.yaml_loader import PyYamlLoader


"""
solid-name: WorkflowCatalogFactory
solid-category: factory
solid-spec: [SPEC-035]
solid-description: Provides a production workflow catalog resolver.
"""
class WorkflowCatalogFactory:
    def make(self) -> WorkflowCatalogResolver:
        return WorkflowCatalogResolver(
            builder=WorkflowCatalogBuilder(
                discoverer=PackageWorkflowSourceDiscoverer(
                    file_loader=YamlConfigFileLoader(loader=PyYamlLoader()),
                    document_decoder=PydanticModelDecoder(
                        model_type=WorkflowPackageCatalogDocument,
                    ),
                ),
                indexer=WorkflowSourceIndexer(),
            )
        )
