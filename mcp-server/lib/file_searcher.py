"""
solid-description: Locates source files by searching for named type declarations or by matching filename patterns across a codebase.
solid-category: utility
solid-tags: [utility, search]
"""

import re
from pathlib import Path
from typing import Optional

from lib.codebase_searcher import iter_source_files

_SOURCE_EXTS = {".swift", ".kt", ".java", ".py", ".ts", ".js"}
_DECL_PATTERN = re.compile(
    r'\b(class|struct|protocol|enum|actor|extension|typealias)\s+{name}\b'
)


def grep_by_name(name: str, directory: Optional[str] = None) -> str:
    """Search file contents for type definitions, extensions, and imports of *name*.

    Finds lines matching: class/struct/protocol/enum/actor/extension/typealias <name>

    Returns a formatted string listing matching files and matched lines.
    """
    root = Path(directory) if directory else Path.cwd()
    if not root.is_dir():
        return f"Error: directory not found: {root}"

    pattern = re.compile(
        r'\b(class|struct|protocol|enum|actor|extension|typealias)\s+' + re.escape(name) + r'\b'
    )

    results = []
    for filepath in iter_source_files(root):
        if filepath.suffix not in _SOURCE_EXTS:
            continue
        try:
            for lineno, line in enumerate(
                filepath.read_text(encoding="utf-8", errors="replace").splitlines(), 1
            ):
                if pattern.search(line):
                    results.append(f"{filepath}:{lineno}: {line.strip()}")
        except OSError:
            continue

    if not results:
        return f"No definitions or extensions of '{name}' found."
    return "\n".join(results)


def glob_by_name(pattern: str, directory: Optional[str] = None) -> str:
    """Search filenames matching a glob pattern.

    Examples:
      glob_by_name("*UserManager*")  → finds UserManager.swift, MockUserManager.swift
      glob_by_name("*Repository*")   → finds all files with 'Repository' in the name

    Returns a newline-separated list of matching file paths.
    """
    root = Path(directory) if directory else Path.cwd()
    if not root.is_dir():
        return f"Error: directory not found: {root}"

    matches = [str(p) for p in iter_source_files(root) if root.rglob(pattern) and p.match(pattern)]

    if not matches:
        return f"No files matching '{pattern}' found."
    return "\n".join(sorted(matches))
