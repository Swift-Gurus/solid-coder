"""Builds structured principle content for detection rules."""

import json
from pathlib import Path
from typing import Callable

from common.xml_block_parser import parse as _parse_xml_blocks
from rules.load_reference import strip_frontmatter as _strip_frontmatter
from rules.principle_content_building import PrincipleContentBuilding
from rules.principle_metrics_example_loading import PrincipleMetricsExampleLoading
from utils.prompt_builder import TextFileReading


class PrincipleContentBuilder(PrincipleContentBuilding):
    """
    solid-name: PrincipleContentBuilder
    solid-category: service
    solid-description: Assembles one principle's definitions, detection procedures, exceptions, schemas, and auditable metric examples.
    """

    def __init__(
        self,
        reader: TextFileReading,
        metrics_loader: PrincipleMetricsExampleLoading,
        xml_parser: Callable[[str], dict] = _parse_xml_blocks,
        frontmatter_stripper: Callable[[str], str] = _strip_frontmatter,
    ) -> None:
        self._reader = reader
        self._metrics_loader = metrics_loader
        self._xml_parser = xml_parser
        self._strip = frontmatter_stripper

    def build(self, p_entry: dict) -> dict:
        rule_path = Path(p_entry["rule_path"])
        raw = self._reader.read(rule_path)
        if raw is None:
            raise FileNotFoundError(rule_path)
        blocks = self._xml_parser(raw)
        name = p_entry["name"]
        if not (blocks["detection"] or blocks["definition"] or blocks["severity-bands"]):
            return {"name": name, "content": self._strip(raw)}
        sections = [f"## {name.upper()}"]
        for mid, text in blocks["definition"].items():
            sections.append(f'<definition id="{mid}">\n{text}\n</definition>')
        for mid, text in blocks["detection"].items():
            sections.append(f'<detection id="{mid}">\n{text}\n</detection>')
        if blocks["exceptions"]:
            sections.append(f'<exceptions principle="{name.upper()}">\n{blocks["exceptions"]}\n</exceptions>')

        metrics_example = self._metrics_loader.load(
            Path(p_entry["folder"]) / "review" / "output.schema.json"
        )

        if metrics_example:
            payload_example = {
                "timestamp": "ISO-8601",
                "files": [{
                    "file_path": "...",
                    "units": [{
                        "unit_name": "...",
                        "unit_kind": "class",
                        "line_start": 0,
                        "line_end": 0,
                        "metrics": {name: metrics_example},
                    }],
                }],
            }
            sections.append(
                "<submission-metrics-example>\n"
                + json.dumps(payload_example, separators=(",", ":"))
                + "\n</submission-metrics-example>"
            )
            sections.append(
                "<schema-references>\n"
                "  Payload structure: references/review-output.schema.json\n"
                f"  Metrics for {name}: {p_entry['folder']}/review/output.schema.json\n"
                "</schema-references>"
            )

        return {
            "name": name,
            "content": "\n\n".join(sections),
            "detection": blocks["detection"],
            "definition": blocks["definition"],
            "severity_bands": blocks["severity-bands"],
            "exceptions": blocks["exceptions"],
            "principle_name": name,
            "metrics_example": metrics_example,
        }
