"""
solid-description: Searches a codebase for reusable types by solid-frontmatter fields, tags, and imports.
solid-category: utility
solid-tags: [utility, search]
"""

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional, Union

from lib.chunker import Chunker

# Build output, dependency caches, and vendored checkouts — never the user's own
# source. `.derivedData` is the same as the default `DerivedData`, just the
# project-local path some Xcode/CI setups use; it holds SwiftPM SourcePackages
# (dependency clones) and git objects. Skipping these is both a large speed win
# and removes dependency-internal noise from results.
SKIP_DIRS = {".git", ".build", "build", "DerivedData", ".derivedData",
             "Pods", "node_modules", ".solid_coder", ".gradle"}
_SKIP_DIRS = SKIP_DIRS  # internal alias
_SPEC_RE = re.compile(r'^SPEC-\d+$', re.IGNORECASE)
_IMPORT_DECL = re.compile(r'^import\s+(\w+)')
_COMMENT_STRIP = re.compile(r'^[/\*#\s]+')
_BINARY_SNIFF_BYTES = 1024

_chunker = Chunker()


def iter_source_files(root: Path):
    """Yield all non-skipped files under *root* recursively.

    Prunes SKIP_DIRS during the walk so the walker never descends into
    .git/Pods/DerivedData/node_modules — on large codebases these hold the
    overwhelming majority of files and are the dominant scan cost.
    """
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        base = Path(dirpath)
        for name in filenames:
            yield base / name


def _read_text_lines(filepath: Path) -> Optional[list]:
    """Read a file as text lines, skipping binaries.

    Returns None for unreadable files or binaries (detected by a NUL byte in
    the first KB). Frontmatter and imports only ever live in UTF-8 text, so a
    NUL-byte sniff is lossless here: it catches every binary regardless of
    extension (including the extensionless compiled assets iOS projects carry),
    while UTF-16 files such as .strings carry no frontmatter to match.

    The head is read first and sniffed *before* the rest of the file is read, so
    binaries are rejected without ever loading their full payload. That bounds
    peak memory when many workers hit large files concurrently. Text files are
    still read in full — frontmatter blocks may appear above every type in a
    file (per the create-type convention), so the whole file must be scanned.
    """
    try:
        with filepath.open("rb") as fh:
            head = fh.read(_BINARY_SNIFF_BYTES)
            if b"\x00" in head:
                return None
            data = head + fh.read()
    except OSError:
        return None
    return data.decode("utf-8", errors="replace").splitlines()


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


def _scan_lines(lines: list) -> tuple:
    """Single pass over a file's lines: extract frontmatter + import names.

    Replaces the previous two full-file passes (one for frontmatter, one for
    imports). Returns (frontmatter_dict, import_names). Import names are kept as
    a list so callers can count per-occurrence, matching prior behaviour.
    """
    fm = {"description": "", "tags": set(), "specs": set()}
    imports = []
    for line in lines:
        stripped = line.strip()
        # Cheap guards before the expensive regex/sub work: the vast majority of
        # lines in a source file are neither an import nor frontmatter. Only the
        # `import`-prefixed lines reach the regex, and only `solid-` lines reach
        # the comment strip. Lossless — every match shape still gets evaluated.
        if stripped.startswith("import"):
            m = _IMPORT_DECL.match(stripped)
            if m:
                imports.append(m.group(1).lower())
            continue
        if "solid-" not in line:
            continue
        inner = _COMMENT_STRIP.sub("", line).strip()
        low = inner.lower()
        if low.startswith("solid-description:"):
            fm["description"] = inner[len("solid-description:"):].strip()
        elif low.startswith("solid-tags:"):
            raw = inner[len("solid-tags:"):].strip().strip("[]")
            fm["tags"].update(t.strip().lower() for t in re.split(r"[,\s]+", raw) if t.strip())
        elif low.startswith("solid-spec:"):
            raw = inner[len("solid-spec:"):].strip().strip("[]")
            fm["specs"].update(s.strip().upper() for s in re.split(r"[,\s]+", raw) if s.strip())
    return fm, imports


def _match_file(filepath: Path, tags_lower: set, spec_numbers: set, min_matches: int):
    lines = _read_text_lines(filepath)
    if lines is None:
        return None

    fm, imports = _scan_lines(lines)

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
    hits += sum(1 for imp in imports if imp in tags_lower)

    return {"path": str(filepath), "description": fm["description"]} if hits >= min_matches else None


def _worker_count() -> int:
    """Thread pool size for the (I/O-bound) file scan, derived from the host."""
    return min(16, (os.cpu_count() or 1) * 2)


def _collect_matches(sources: Path, all_tags: set, all_specs: set, min_matches: int) -> dict:
    """Scan source files and return raw matches list plus total file count.

    Per-file work (open, read, decode, scan) is I/O-bound, so it runs across a
    thread pool. ThreadPoolExecutor.map preserves input order, keeping output
    deterministic (walk order) regardless of which worker finishes first.

    NOTE: this scan is deliberately pure Python, not a shell-out to grep/rg. A
    plugin ships to arbitrary machines where ripgrep is often absent (bundled
    only inside app packages) and `grep` resolves to GNU/BSD/ugrep variants with
    divergent flags. Portability, not raw throughput, is why we own the scan.
    """
    files = list(iter_source_files(sources))
    with ThreadPoolExecutor(max_workers=_worker_count()) as ex:
        results = ex.map(lambda fp: _match_file(fp, all_tags, all_specs, min_matches), files)
        matches = [m for m in results if m]
    return {"matches": matches, "total": len(files)}


def _resolve_search_params(
    sources_dir: Optional[str],
    plan_path: Optional[str],
    tags: Optional[list],
    spec_numbers: Optional[list],
) -> Union[tuple, str]:
    """Resolve and validate search parameters. Returns (sources, all_tags, all_specs) or error str."""
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

    return sources, all_tags, all_specs


def search(
    sources_dir: Optional[str] = None,
    plan_path: Optional[str] = None,
    tags: Optional[list] = None,
    spec_numbers: Optional[list] = None,
    min_matches: int = 3,
) -> str:
    """Search a directory for files matching the given tags or spec numbers.

    Returns a human-readable string suitable for LLM consumption.
    sources_dir defaults to the current working directory when omitted.
    """
    params = _resolve_search_params(sources_dir, plan_path, tags, spec_numbers)
    if isinstance(params, str):
        return params

    sources, all_tags, all_specs = params
    raw = _collect_matches(sources, all_tags, all_specs, min_matches)

    if not raw["matches"]:
        return f"No files matched in {sources} ({raw['total']} files scanned)."

    lines = [
        f"Codebase files matching your search ({len(raw['matches'])} of {raw['total']} scanned).",
        "Review descriptions to assess relevance. Use the Read tool to inspect any file in full.",
        "",
    ]
    for m in raw["matches"]:
        desc = m.get("description", "")
        spec_tag = f"  [{', '.join(m['matched_specs'])}]" if m.get("matched_specs") else ""
        lines.append(f"{m['path']}{spec_tag}" + (f" — {desc}" if desc else ""))

    return _chunker.chunk("\n".join(lines), "search-results")


def search_raw(
    sources_dir: Optional[str] = None,
    plan_path: Optional[str] = None,
    tags: Optional[list] = None,
    spec_numbers: Optional[list] = None,
    min_matches: int = 1,
) -> dict:
    """Like search() but returns a structured dict for CLI/JSON consumers."""
    params = _resolve_search_params(sources_dir, plan_path, tags, spec_numbers)
    if isinstance(params, str):
        return {"error": params, "matches": []}

    sources, all_tags, all_specs = params
    raw = _collect_matches(sources, all_tags, all_specs, min_matches)
    return {
        "matches": raw["matches"],
        "summary": {"total_files_scanned": raw["total"], "files_matched": len(raw["matches"])},
    }
