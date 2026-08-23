"""Reads canonical instruction blocks for rule-migration parity tests."""


"""
solid-name: RuleInstructionBlockReader
solid-category: test-support
solid-spec: [SPEC-039]
solid-description: Extracts authored detection and exception bodies for workflow migration parity assertions.
"""
class RuleInstructionBlockReader:
    def detection(self, content: str, metric_id: str, name: str) -> str:
        named_opening = f'<detection id="{metric_id}" name="{name}">'
        opening = (
            named_opening
            if named_opening in content
            else f'<detection id="{metric_id}">'
        )
        return self._body(
            content,
            opening,
            "detection",
        )

    def exceptions(self, content: str) -> str:
        return self._body(content, "<exceptions>", "exceptions")

    def _body(self, content: str, opening: str, tag: str) -> str:
        body_start = content.index(opening) + len(opening)
        body_end = content.index(f"</{tag}>", body_start)
        return content[body_start:body_end].strip()
