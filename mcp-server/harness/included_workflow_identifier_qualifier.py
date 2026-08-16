"""Qualifies an included workflow identifier for one runtime instance."""

from harness.included_workflow_identifier_qualifying import (
    IncludedWorkflowIdentifierQualifying,
)


"""
solid-name: IncludedWorkflowIdentifierQualifier
solid-category: service
solid-spec: [SPEC-037]
solid-description: Qualifies child workflow identifiers under a stable runtime instance prefix.
"""
class IncludedWorkflowIdentifierQualifier(IncludedWorkflowIdentifierQualifying):
    def qualify(
        self,
        identifier: str,
        alias: str,
        instance_prefix: str,
    ) -> str:
        local_id = identifier.removeprefix(f"{alias}.")
        return f"{instance_prefix}.{local_id}"
