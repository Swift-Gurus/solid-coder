"""Defines the stable public identity format shared by workflow contracts."""

from typing import Annotated

from pydantic import StringConstraints


"""
solid-name: WorkflowId
solid-category: model
solid-spec: [SPEC-035, SPEC-039]
solid-description: Constrains stable workflow identifiers shared by packages, catalogs, policies, and audit records.
"""
WorkflowId = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z0-9]+(?:[-/][a-z0-9]+)*$"),
]
