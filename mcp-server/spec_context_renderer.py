"""Renders specification ancestry as readable command-line context."""

from spec_context_rendering import SpecContextRendering


"""
solid-name: SpecContextRenderer
solid-category: boundary-adapter
solid-description: Renders specification ancestry records as readable context.
"""
class SpecContextRenderer(SpecContextRendering):
    def render(self, spec_number: str, specs: list[dict]) -> str:
        if not specs:
            return "No ancestors found."
        separator = "=" * 72
        lines = [
            separator,
            f"  SPEC CONTEXT: {spec_number} ({len(specs)} specs in chain)",
            separator,
        ]
        subsection = "-" * 40
        for spec in specs:
            lines.append(f"\n{spec.get('number', '?')} — {spec.get('feature', '?')}")
            lines.append(f"Status: {spec.get('status', '?')}")
            if spec.get("content"):
                lines.append(subsection)
                lines.append(spec["content"].strip())
        lines.extend([separator, "  END OF SPEC CONTEXT", separator])
        return "\n".join(lines)
