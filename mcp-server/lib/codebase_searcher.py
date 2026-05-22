"""
solid-description: Searches a codebase for reusable types by solid-frontmatter fields, tags, and imports.
solid-category: utility
solid-tags: [utility, search]
"""

import json
import re
from pathlib import Path
from typing import Optional

from lib.chunker import Chunker

_SKIP_DIRS = {".git", ".build", "build", "DerivedData", "Pods", "node_modules", ".solid_coder"}
_SPEC_RE = re.compile(r'^SPEC-\d+$', re.IGNORECASE)
_IMPORT_DECL = re.compile(r'^import\s+(\w+)')
_COMMENT_STRIP = re.compile(r'^[/\*#\s]+')

_chunker = Chunker()


def extract_plan_terms(plan_path: Path) -> tuple:
    """Extract search terms and spec numbers from arch.json or implementation-plan.json."""
    try:
        data = json.loads(plan_path.read_text(encoding="utf-8"))
    except Exception:
        return [], []
    terms, specs = [], []
    for comp in data.get("components", []):
        for key in ("name", "category"):
            v = comp.get(key, "")
            if v:
                terms.append(v)
        for iface in comp.get("interfaces", []) + comp.get("dependencies", []):
            terms.append(iface)
        terms.extend(comp.get("stack", []))
    for item in data.get("plan_items", []):
        if item.get("component"):
            terms.append(item["component"])
    if data.get("spec_number"):
        specs.append(data["spec_number"])
    return list(dict.fromkeys(t for t in terms if t)), specs


def _frontmatter_fields(lines: list) -> dict:
    result = {"description": "", "tags": set(), "specs": set()}
    for line in lines:
        inner = _COMMENT_STRIP.sub("", line).strip()
        low = inner.lower()
        if low.startswith("solid-description:"):
            result["description"] = inner[len("solid-description:"):].strip()
        elif low.startswith("solid-tags:"):
            raw = inner[len("solid-tags:"):].strip().strip("[]")
            result["tags"].update(t.strip().lower() for t in re.split(r"[,\s]+", raw) if t.strip())
        elif low.startswith("solid-spec:"):
            raw = inner[len("solid-spec:"):].strip().strip("[]")
            result["specs"].update(s.strip().upper() for s in re.split(r"[,\s]+", raw) if s.strip())
    return result


def _match_file(filepath: Path, tags_lower: set, spec_numbers: set, min_matches: int):
    try:
        lines = filepath.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None

    fm = _frontmatter_fields(lines)

    matched_specs = sorted(fm["specs"] & spec_numbers) if spec_numbers else []
    if matched_specs:
        return {"path": str(filepath), "description": fm["description"], "matched_specs": matched_specs}

    if not tags_lower:
        return None

    hits = 0
    if fm["description"]:
        desc_words = {w.lower() for w in re.split(r"\W+", fm["description"]) if w}
        hits += len(desc_words & tags_lower)
    if fm["tags"]:
        hits += len(fm["tags"] & tags_lower)
    for line in lines:
        m = _IMPORT_DECL.match(line.strip())
        if m and m.group(1).lower() in tags_lower:
            hits += 1

    return {"path": str(filepath), "description": fm["description"]} if hits >= min_matches else None


def search(
    sources_dir: Optional[str] = None,
    plan_path: Optional[str] = None,
    tags: Optional[list] = None,
    spec_numbers: Optional[list] = None,
    min_matches: int = 3,
) -> str:
    """Search a directory for files matching the given tags or spec numbers.

    sources_dir defaults to the current working directory when omitted.
    """
    sources = Path(sources_dir) if sources_dir else Path.cwd()
    if not sources.is_dir():
        return f"Error: sources_dir not found: {sources}"

    auto_terms, auto_specs = (extract_plan_terms(Path(plan_path)) if plan_path else ([], []))

    all_tags: set = set()
    all_specs: set = set(s.upper() for s in ((spec_numbers or []) + auto_specs) if s)
    for t in (tags or []) + auto_terms:
        if not t:
            continue
        if _SPEC_RE.match(t):
            all_specs.add(t.upper())
        else:
            all_tags.add(t.lower())

    if not all_tags and not all_specs:
        return "Error: provide plan_path, tags, or spec_numbers to search."

    matches = []
    total = 0
    for filepath in sources.rglob("*"):
        if not filepath.is_file():
            continue
        if any(part in _SKIP_DIRS for part in filepath.parts):
            continue
        total += 1
        match = _match_file(filepath, all_tags, all_specs, min_matches)
        if match:
            matches.append(match)

    if not matches:
        return f"No files matched in {sources} ({total} files scanned)."

    lines = [
        f"Codebase files matching your search ({len(matches)} of {total} scanned).",
        "Review descriptions to assess relevance. Use the Read tool to inspect any file in full.",
        "",
    ]
    for m in matches:
        desc = m.get("description", "")
        spec_tag = f"  [{', '.join(m['matched_specs'])}]" if m.get("matched_specs") else ""
        lines.append(f"{m['path']}{spec_tag}" + (f" — {desc}" if desc else ""))

    return _chunker.chunk("\n".join(lines), "search-results")
