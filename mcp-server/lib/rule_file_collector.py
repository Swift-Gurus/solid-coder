#!/usr/bin/env python3
"""
solid-description: Collects rule file paths for a principle based on profile and
exclusion set. Shared by mcp-server/server.py and docs/server.py to eliminate
duplicated file-path collection logic. Returns an ordered list of absolute file
paths for a given principle folder, profile, and exclusion set.
solid-category: utility
solid-tags: [utility, service]
"""

from pathlib import Path
from typing import Optional

_PROFILE_INSTR_DIR: dict[str, str] = {"review": "review", "code": "fix"}
_PROFILE_INCLUDE_CODE: dict[str, bool] = {"review": False, "code": True}


def collect_files(
    folder: Path,
    rule_path: str,
    exclude: set,
    profile: str,
    parse_frontmatter=None,
) -> list[str]:
    """Collect all rule file paths for one principle entry.

    Args:
        folder:           Principle folder path.
        rule_path:        Path to rule.md.
        exclude:          Set of lowercase section names to skip.
        profile:          Pipeline profile ('review' or 'code').
        parse_frontmatter: Optional frontmatter parser; if None, required_patterns are skipped.

    Returns:
        Ordered list of absolute file path strings.
    """
    instr_dir = _PROFILE_INSTR_DIR.get(profile, "fix")
    include_code = _PROFILE_INCLUDE_CODE.get(profile, False)
    paths: list[str] = []

    if "rule" not in exclude:
        paths.append(rule_path)
    if "instructions" not in exclude:
        instr = folder / instr_dir / "instructions.md"
        if instr.is_file():
            paths.append(str(instr))
    if "code_rules" not in exclude and include_code:
        code_rule = folder / "code" / "instructions.md"
        if code_rule.is_file():
            paths.append(str(code_rule))
    if "examples" not in exclude:
        examples_dir = folder / "Examples"
        if examples_dir.is_dir():
            for f in sorted(examples_dir.iterdir()):
                if f.is_file():
                    paths.append(str(f))
    if "patterns" not in exclude and parse_frontmatter is not None:
        try:
            fm = parse_frontmatter.parse(rule_path)
            for pp in (fm.get("required_patterns") or []):
                if isinstance(pp, str) and Path(pp).is_file():
                    paths.append(pp)
        except Exception:
            pass

    return paths
