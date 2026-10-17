from harness.pydantic_type_adapter_encoder import StructuredModelEncoding
from hook_permission_response import HookPermissionResponse


"""
solid-name: HookPermissionResponseEncoder
solid-category: adapter
solid-description: Encodes hook permission decisions, response context, and corrected input into the hook wire format.
"""
class HookPermissionResponseEncoder(StructuredModelEncoding[HookPermissionResponse]):
    def encode(self, value: HookPermissionResponse) -> object:
        decision = value.decision
        hook_output: dict[str, object] = {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow" if decision.allow else "deny",
        }
        if not decision.allow:
            hook_output["permissionDecisionReason"] = decision.reason or ""
        if decision.additional_context:
            hook_output["additionalContext"] = decision.additional_context
        if decision.allow and value.updated_input is not None:
            hook_output["updatedInput"] = value.updated_input
        return {"hookSpecificOutput": hook_output}
