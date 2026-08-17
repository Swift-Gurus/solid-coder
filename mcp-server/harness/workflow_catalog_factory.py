"""Assembles the production workflow catalog resolver."""

from __future__ import annotations

from harness.package_workflow_source_discoverer import PackageWorkflowSourceDiscoverer
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.pydantic_model_decoder import PydanticModelDecoder
from harness.workflow_catalog_builder import WorkflowCatalogBuilder
from harness.workflow_catalog_resolver import WorkflowCatalogResolver
from harness.workflow_package_catalog_document import WorkflowPackageCatalogDocument
from harness.workflow_source_indexer import WorkflowSourceIndexer
from scoring.yaml_config_file_loader import YamlConfigFileLoader
from scoring.yaml_loader import PyYamlLoader


def make_workflow_catalog_builder() -> WorkflowCatalogBuilder:
    file_loader = YamlConfigFileLoader(loader=PyYamlLoader())
    return WorkflowCatalogBuilder(
        discoverer=PackageWorkflowSourceDiscoverer(
            file_loader=file_loader,
            document_decoder=PydanticModelDecoder(
                model_type=WorkflowPackageCatalogDocument,
                error_factory=FlowValidationErrorFactory(),
            ),
        ),
        indexer=WorkflowSourceIndexer(),
    )


def make_workflow_catalog_resolver() -> WorkflowCatalogResolver:
    return WorkflowCatalogResolver(builder=make_workflow_catalog_builder())
