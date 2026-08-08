"""Defines formatting of violation responses returned to review workers."""

from typing import Protocol


"""
solid-name: ViolationResponseFormatting
solid-category: abstraction
solid-description: Contract for formatting violations into a model-facing response.
"""
class ViolationResponseFormatting(Protocol):
    def format(self, violations: list, output_dir: str) -> dict: ...


"""
solid-name: ViolationResponseFormatter
solid-category: service
solid-description: Formats severe violations and the required fix-submission instructions.
"""
class ViolationResponseFormatter(ViolationResponseFormatting):
    def format(self, violations: list, output_dir: str) -> dict:
        response: dict = {"violations": violations}
        if violations:
            rule_ids = ", ".join(f"'{violation['rule_id']}'" for violation in violations)
            response["output_dir"] = output_dir
            response["message"] = (
                f"Found {len(violations)} SEVERE violation(s). Complete these steps:\n"
                f"1. Call mcp__docs__load_fix_for_violation ONCE with metric_ids=[{rule_ids}] "
                f"to get all fix strategies in one call.\n"
                f"2. For each violation, prepare a concrete code-specific fix using the guidance.\n"
                f"3. Call mcp__pipeline__submit_fix ONCE with output_dir='{output_dir}' and "
                f"fixes=[{{rule_id, file_path, unit_name, suggested_fix}}, ...] for all violations."
            )
        return response
