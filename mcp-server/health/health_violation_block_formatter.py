"""Formats typed workflow health violations for write blocking."""

from health_violation import HealthViolation

"""
solid-name: HealthViolationBlockFormatter
solid-category: service
solid-spec: [SPEC-036]
solid-description: Formats severe health findings with correction guidance while keeping audit evidence out of the model-facing response.
"""


class HealthViolationBlockFormatter:
    def format_block_reason(
        self,
        violations: list[HealthViolation],
    ) -> str:
        lines = [f"{len(violations)} SEVERE violation(s) found:\n"]
        for violation in violations:
            issue_lines = violation.issue.splitlines()
            lines.append(
                f"  • {violation.principle} / {violation.metric_id} — {issue_lines[0]}"
            )
            lines.extend(f"    {line}" for line in issue_lines[1:])
            if violation.fix:
                lines.append(f"    Suggested fix: {violation.fix}")
            lines.append("")
        lines.append(
            "Fix all violations before writing. The gate will block again on "
            "any remaining SEVERE violation."
        )
        return "\n".join(lines)
