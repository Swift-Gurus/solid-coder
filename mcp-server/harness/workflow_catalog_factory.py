"""Assembles the production workflow catalog resolver."""

from __future__ import annotations

from harness.workflow_catalog_builder import WorkflowCatalogBuilder
from harness.workflow_catalog_resolver import WorkflowCatalogResolver
from harness.workflow_package_validator import WorkflowPackageValidator
from harness.workflow_source_discoverer import WorkflowSourceDiscoverer
from harness.workflow_source_indexer import WorkflowSourceIndexer
from scoring.yaml_config_file_loader import YamlConfigFileLoader
from scoring.yaml_loader import PyYamlLoader


def make_workflow_catalog_resolver() -> WorkflowCatalogResolver:
    file_loader = YamlConfigFileLoader(loader=PyYamlLoader())
    return WorkflowCatalogResolver(
        builder=WorkflowCatalogBuilder(
            discoverer=WorkflowSourceDiscoverer(
                file_loader=file_loader,
                package_validator=WorkflowPackageValidator(),
            ),
            indexer=WorkflowSourceIndexer(),
        )
    )
