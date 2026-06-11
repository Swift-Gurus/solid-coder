"""solid-description: Builds principle content for detection rules.
solid-category: service
solid-tags: [utility, service]
"""

import json
from pathlib import Path
from typing import Callable, Optional, Protocol

from common.xml_block_parser import parse as _parse_xml_blocks
from rules.load_reference import strip_frontmatter as _strip_frontmatter


def _minimal_value_for_schema(prop_schema: dict):
    t = prop_schema.get("type", "string")
    if t == "integer":
        return 0
    if t == "string":
        enum = prop_schema.get("enum")
        return enum[0] if enum else "example"
    if t == "boolean":
        return False
    if t == "array":
        items = prop_schema.get("items", {})
        item_props = items.get("properties", {})
        if item_props:
            return [{k: _minimal_value_for_schema(v) for k, v in item_props.items()}]
        return []
    if t == "object":
        props = prop_schema.get("properties", {})
        if props:
            return {k: _minimal_value_for_schema(v) for k, v in props.items()}
        return {}
    return "example"


def _default_parse_schema(schema_path) -> Optional[dict]:
    p = Path(str(schema_path))
    if not p.exists():
        return None
    try:
        schema = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None
    required = schema.get("required", [])
    props = schema.get("properties", {})
    if not required:
        return None
    metrics_example: dict = {}
    for var_name in required:
        var_schema = props.get(var_name, {})
        value_schema = var_schema.get("properties", {}).get("value", {})
        metrics_example[var_name] = {"value": _minimal_value_for_schema(value_schema)}
    return {"metrics_example": metrics_example}


class PrincipleContentBuilding(Protocol):
    def build(self, p_entry: dict) -> dict: ...


class PrincipleContentBuilder:
    """Reads a principle's rule.md and assembles its detection-rules output dict."""

    def __init__(
        self,
        xml_parser: Optional[Callable[[str], dict]] = None,
        schema_loader: Optional[Callable[[Path], Optional[dict]]] = None,
        frontmatter_stripper: Optional[Callable[[str], str]] = None,
    ) -> None:
        self._xml_parser = xml_parser or _parse_xml_blocks
        self._schema_loader = schema_loader or _default_parse_schema
        self._strip = frontmatter_stripper or _strip_frontmatter

    def build(self, p_entry: dict) -> dict:
        raw = Path(p_entry["rule_path"]).read_text(encoding="utf-8")
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

        schema_path = Path(p_entry["folder"]) / "review" / "output.schema.json"
        parsed_schema = self._schema_loader(schema_path)
        metrics_example: dict = parsed_schema["metrics_example"] if parsed_schema else {}

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
