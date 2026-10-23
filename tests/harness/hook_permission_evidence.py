"""Decodes the public pre-write hook response for live assertions."""

from typing import Literal

from pydantic import AliasPath, BaseModel, ConfigDict, Field

"""
solid-name: HookPermissionEvidence
solid-category: test-support
solid-spec: [SPEC-050]
solid-description: Projects the hook wire response into its event, permission, and diagnostic fields without interpreting a denial as a successful review.
"""


class HookPermissionEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    event: Literal["PreToolUse"] = Field(
        validation_alias=AliasPath("hookSpecificOutput", "hookEventName"),
    )
    decision: Literal["allow", "deny"] = Field(
        validation_alias=AliasPath("hookSpecificOutput", "permissionDecision"),
    )
    reason: str = Field(
        default="",
        validation_alias=AliasPath("hookSpecificOutput", "permissionDecisionReason"),
    )
