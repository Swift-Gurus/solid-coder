"""Selects automatically enrolled rules from the existing workflow catalog."""

from typing import Protocol

from harness.workflow_catalog_resolving import WorkflowCatalogResolving
from harness.workflow_source import WorkflowSource


"""
solid-name: EnrolledRuleSourcesSelecting
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for selecting ordered workflow sources eligible for automatic rule-set inclusion.
"""
class EnrolledRuleSourcesSelecting(Protocol):
    def select(self, search_paths: list[str]) -> list[WorkflowSource]: ...


"""
solid-name: EnrolledRuleSourcesSelector
solid-category: service
solid-spec: [SPEC-039]
solid-description: Reuses catalog ordering and retains only automatically included review rules.
"""
class EnrolledRuleSourcesSelector(EnrolledRuleSourcesSelecting):
    def __init__(self, catalog_resolver: WorkflowCatalogResolving) -> None:
        self._catalog_resolver = catalog_resolver

    def select(self, search_paths: list[str]) -> list[WorkflowSource]:
        return [source for source in self._catalog_resolver.catalog(search_paths).rule_sources()
                if source.rule is not None and source.rule.auto_include]
