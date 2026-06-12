"""
solid-description: Assembles the LLM health-check prompt from detection rules and file content.
solid-category: service
solid-tags: [hook, llm]
"""

from typing import Optional, Protocol

from hook_utils import PLUGIN_ROOT
from prompt_builder import BasePromptBuilder, PromptReading

_PROMPTS_DIR = PLUGIN_ROOT / "mcp-server" / "prompts" / "health-check"

_HC_UNIT_KINDS: dict = {
    "isp": "protocol",
}

_HC_COMPLIANT_METRICS: dict = {
    "isp": {
        "width": {"value": 1},
        "min_coverage": {"value": 100},
        "cohesion_groups": {"value": 1},
    },
}


class PromptBuilding(Protocol):
    def build(
        self,
        principles: list,
        content: str,
        path: str,
        parent_session_id: str,
        output_dir: str,
    ) -> str: ...


class HealthPromptBuilder(BasePromptBuilder):
    """Assembles the LLM health-check prompt from detection rules and file content."""

    def __init__(
        self,
        reader: Optional[PromptReading] = None,
        shared_reader: Optional[PromptReading] = None,
    ) -> None:
        super().__init__(reader=reader, shared_reader=shared_reader, prompts_dir=_PROMPTS_DIR)

    def build(
        self,
        principles: list,
        content: str,
        path: str,
        parent_session_id: str,
        output_dir: str = "",
    ) -> str:
        detection_instructions = "\n\n---\n\n".join(
            p["content"] for p in principles if p.get("content")
        )
        batch_example = self._make_batch_example(principles, output_dir)
        workflow = (
            self._read("workflow.md")
            .replace("{file_path}", path)
            .replace("{output_dir}", output_dir)
            .replace("{submit_batch_example}", batch_example)
        )
        return self._header(parent_session_id) + (
            self._read("preamble.md")
            + "\n\n<detection-instructions>\n"
            + detection_instructions
            + "\n</detection-instructions>"
            + "\n\n<code-to-review>\n"
            + content
            + "\n</code-to-review>"
            + "\n\n"
            + workflow
            + "\n\n"
            + self._read("output-format.md")
            + "\n\n"
            + self._read_shared("constraints.md")
        )

    def _make_batch_example(self, principles: list, output_dir: str) -> str:
        import json as _json
        submissions = {}
        for p in principles:
            agent = p.get("name", "")
            metrics_example = p.get("metrics_example", {})
            if not agent:
                continue
            unit_kind = _HC_UNIT_KINDS.get(agent, "class")
            unit_name = "MyProtocol" if unit_kind == "protocol" else "ClassName"
            principle_metrics = _HC_COMPLIANT_METRICS.get(agent, metrics_example)
            unit = {
                "unit_name": unit_name,
                "unit_kind": unit_kind,
                "metrics": {agent: principle_metrics},
            }
            submissions[agent] = {
                "timestamp": "2026-06-05T10:00:00Z",
                "files": [{"file_path": "/path/to/ReviewedFile.swift", "units": [unit]}],
            }
        example = {
            "output_dir": output_dir or "/path/to/gate/session",
            "submissions": submissions,
        }
        return _json.dumps(example, indent=2)
