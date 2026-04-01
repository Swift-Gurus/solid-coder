#!/usr/bin/env python3
"""Parse YAML frontmatter from a markdown file and output as JSON.

Resolves relative path references to absolute paths based on the file's
parent directory and an optional references root.

Usage:
    python3 parse-frontmatter.py <file> [--refs-root <path>]

Output (stdout):
    JSON object with all frontmatter fields, paths resolved to absolute.

Exit codes:
    0 — success
    1 — error (missing file, no frontmatter, invalid YAML)
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


# Fields whose values are file paths relative to the file's parent directory
LOCAL_PATH_FIELDS = {"rules", "output_schema", "input_schema", "examples", "code"}

# Fields whose values are paths relative to the references root
REFS_PATH_FIELDS = {"required_patterns"}

# Placeholder token used in instruction frontmatter
PRINCIPLE_FOLDER_TOKEN = "PRINCIPLE_FOLDER_ABSOLUTE_PATH"


def parse_yaml_simple(text: str) -> Dict[str, Any]:
    """Minimal YAML parser for flat frontmatter with optional lists.

    Supports:
      - key: value (string)
      - key:           (followed by list items)
        - item1
        - item2
    """
    result: Dict[str, Any] = {}
    current_key: Optional[str] = None
    current_list: Optional[List[str]] = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # List item
        if stripped.startswith("- ") and current_key is not None:
            if current_list is None:
                current_list = []
            current_list.append(stripped[2:].strip())
            continue

        # Flush previous list
        if current_key is not None and current_list is not None:
            result[current_key] = current_list
            current_list = None
            current_key = None

        # Key-value pair
        if ":" in stripped:
            colon_idx = stripped.index(":")
            key = stripped[:colon_idx].strip()
            value = stripped[colon_idx + 1:].strip()

            if value:
                # Inline array: [item1, item2]
                if value.startswith("[") and value.endswith("]"):
                    inner = value[1:-1].strip()
                    if inner:
                        result[key] = [item.strip() for item in inner.split(",")]
                    else:
                        result[key] = []
                # Scalar value — handle booleans and numbers
                elif value.lower() in ("true", "yes"):
                    result[key] = True
                elif value.lower() in ("false", "no"):
                    result[key] = False
                else:
                    try:
                        result[key] = int(value)
                    except ValueError:
                        result[key] = value
                current_key = None
                current_list = None
            else:
                # Empty value — might be followed by a list
                current_key = key
                current_list = None

    # Flush final list
    if current_key is not None and current_list is not None:
        result[current_key] = current_list
    elif current_key is not None:
        result[current_key] = None

    return result


def extract_frontmatter(content: str) -> Optional[str]:
    """Extract YAML frontmatter between --- delimiters."""
    if not content.startswith("---"):
        return None
    end = content.find("---", 3)
    if end == -1:
        return None
    return content[3:end].strip()


def resolve_path(value: str, base_dir: Path) -> str:
    """Resolve a relative path against a base directory."""
    p = Path(value)
    if p.is_absolute():
        return str(p)
    resolved = (base_dir / p).resolve()
    return str(resolved)


def resolve_paths(
    data: Dict[str, Any],
    file_dir: Path,
    refs_root: Optional[Path],
) -> Dict[str, Any]:
    """Resolve path fields to absolute paths."""
    result = dict(data)

    # Replace PRINCIPLE_FOLDER_ABSOLUTE_PATH token in all string values
    for key, value in result.items():
        if isinstance(value, str) and PRINCIPLE_FOLDER_TOKEN in value:
            result[key] = value.replace(PRINCIPLE_FOLDER_TOKEN, str(file_dir.parent))

    # Resolve local path fields
    for field in LOCAL_PATH_FIELDS:
        if field not in result:
            continue
        value = result[field]
        if isinstance(value, str):
            result[field] = resolve_path(value, file_dir)
        elif isinstance(value, list):
            result[field] = [resolve_path(v, file_dir) for v in value]

    # Resolve refs-root path fields
    if refs_root:
        for field in REFS_PATH_FIELDS:
            if field not in result:
                continue
            value = result[field]
            if isinstance(value, str):
                result[field] = resolve_path(
                    f"design_patterns/{value}.md", refs_root
                )
            elif isinstance(value, list):
                result[field] = [
                    resolve_path(f"design_patterns/{v}.md", refs_root)
                    for v in value
                ]

    return result


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file> [--refs-root <path>]", file=sys.stderr)
        sys.exit(1)

    file_path = Path(sys.argv[1])
    refs_root: Optional[Path] = None

    if "--refs-root" in sys.argv:
        idx = sys.argv.index("--refs-root")
        if idx + 1 < len(sys.argv):
            refs_root = Path(sys.argv[idx + 1]).resolve()

    if not file_path.exists():
        print(f"Error: {file_path} not found", file=sys.stderr)
        sys.exit(1)

    content = file_path.read_text(encoding="utf-8")
    yaml_text = extract_frontmatter(content)

    if yaml_text is None:
        print(f"Error: no frontmatter found in {file_path}", file=sys.stderr)
        sys.exit(1)

    data = parse_yaml_simple(yaml_text)
    file_dir = file_path.resolve().parent

    # Default refs-root to grandparent of the file
    # (e.g., references/SRP/rule.md → refs-root = references/)
    if refs_root is None and REFS_PATH_FIELDS & data.keys():
        refs_root = file_dir.parent

    # Default examples to ["Examples"] when not specified
    if "examples" not in data:
        default_examples = file_dir / "Examples"
        if default_examples.is_dir():
            data["examples"] = ["Examples"]

    # Default code to ["code"] when not specified
    if "code" not in data:
        default_code = file_dir / "code"
        if default_code.is_dir():
            data["code"] = ["code"]

    resolved = resolve_paths(data, file_dir, refs_root)

    # Add source metadata
    resolved["_source"] = str(file_path.resolve())
    resolved["_dir"] = str(file_dir)

    # Build files_to_load — flat list of all files the consumer should read
    files_to_load: List[str] = []
    for field in ("required_patterns", "examples", "rules", "code"):
        value = resolved.get(field)
        if value is None:
            continue
        paths = [value] if isinstance(value, str) else value
        for p in paths:
            pp = Path(p)
            if pp.is_dir():
                files_to_load.extend(
                    str(f) for f in sorted(pp.iterdir()) if f.is_file()
                )
            elif pp.is_file():
                files_to_load.append(str(pp))
            else:
                # Path doesn't exist yet — include it anyway so consumer sees it
                files_to_load.append(str(pp))
    if files_to_load:
        resolved["files_to_load"] = files_to_load

    print(json.dumps(resolved, indent=2))


if __name__ == "__main__":
    main()
