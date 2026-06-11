"""
solid-description: Standardizes and formats violation data from multiple sources for quality gate evaluation and reporting.
solid-category: service
solid-tags: [hook, parsing]
"""

import sys
from pathlib import Path
from typing import Optional, Protocol

_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from hook_utils import ListValidator, ViolationDictValidator, parse_json_field


class LLMResponseParsing(Protocol):
    def parse(self, raw: str) -> Optional[list]: ...


class BlockReasonFormatting(Protocol):
    def format_block_reason(self, violations: list) -> str: ...


class ViolationParsing(LLMResponseParsing, BlockReasonFormatting, Protocol):
    """Composition protocol: combines LLMResponseParsing and BlockReasonFormatting.

    ISP note: composition of two compliant narrow protocols — not a fat interface.
    Retained for backward compatibility with existing callers.
    """


class LLMViolationParser:
    """Parses a violations list from raw LLM text response using structural validation."""

    def parse(self, raw: str) -> Optional[list]:
        violations = parse_json_field(raw, "violations", ListValidator())
        if violations is None:
            return None
        validator = ViolationDictValidator()
        return [v for v in violations if validator.validate(v) is not None]


class ViolationBlockFormatter:
    """Formats a violations list into a human-readable block reason string."""

    def format_block_reason(self, violations: list) -> str:
        count = len(violations)
        lines = [f"{count} SEVERE violation(s) found:\n"]
        for v in violations:
            principle = v.get("principle", "")
            issue_lines = v["issue"].splitlines()
            first = f"{principle} — {issue_lines[0]}" if principle else issue_lines[0]
            lines.append(f"  • {first}")
            for extra in issue_lines[1:]:
                lines.append(f"  {extra}")
            fix = v.get("fix", "")
            if fix:
                lines.append(f"    Suggested fix: {fix}")
            lines.append("")
        lines.append(
            "Fix all violations before writing. "
            "The gate will block again on any remaining SEVERE violation."
        )
        return "\n".join(lines)


class ViolationParser:
    """Facade: delegates LLM response parsing to LLMResponseParsing and formatting to BlockReasonFormatting."""

    def __init__(
        self,
        parser: Optional[LLMResponseParsing] = None,
        formatter: Optional[BlockReasonFormatting] = None,
    ) -> None:
        self._parser: LLMResponseParsing = parser or LLMViolationParser()
        self._formatter: BlockReasonFormatting = formatter or ViolationBlockFormatter()

    def parse(self, raw: str) -> Optional[list]:
        return self._parser.parse(raw)

    def format_block_reason(self, violations: list) -> str:
        return self._formatter.format_block_reason(violations)
