"""Strip review-only content from rule.md for non-review modes.

Rule docs contain both:
  - Rule statements and constraints  (useful for writing code)
  - Detection checklists, scoring, severity bands  (useful only for review)

This module removes the review-only content so code/planner/synth modes load
a lean rule doc. Stripping is deterministic and configured from modes.py.

Two levels of stripping:
  1. H2 sections matching STRIP_H2_SECTIONS are removed entirely
     (e.g. "## Quantitative Metrics Summary")
  2. Bold-labeled subsections matching STRIP_BOLD_SUBSECTIONS are removed
     within each retained block (e.g. "**Detection:**" through to next
     blank-line-separated block or the next bold-label/header)
"""

import re
from typing import List


def strip_header_sections(text: str, names: List[str], level: int) -> str:
    """Remove sections of a given header level whose title matches any name.

    A section starts at the matching header and ends at the next header of the
    same or higher level (exclusive) or end-of-file.

    Args:
        level: 2 for ## headers, 3 for ### headers
    """
    if not names:
        return text

    hashes = "#" * level
    # Match any header at this level or HIGHER (fewer hashes = higher priority)
    same_or_higher = re.compile(rf"^#{{1,{level}}}\s")
    name_patterns = [re.compile(rf"^{re.escape(hashes)}\s+{re.escape(n)}\s*:?\s*$") for n in names]

    lines = text.splitlines(keepends=True)
    result: List[str] = []
    skip = False

    for line in lines:
        if same_or_higher.match(line):
            # New header at same or higher level — check if we should start or stop skipping
            if any(p.match(line.rstrip()) for p in name_patterns):
                skip = True
                continue
            else:
                skip = False

        if not skip:
            result.append(line)

    return "".join(result)


def strip_h2_sections(text: str, names: List[str]) -> str:
    """Remove H2 sections whose header matches any name in `names`."""
    return strip_header_sections(text, names, level=2)


def strip_h3_sections(text: str, names: List[str]) -> str:
    """Remove H3 sections whose header matches any name in `names`.

    An H3 section ends at the next H3, H2, or H1.
    """
    return strip_header_sections(text, names, level=3)


def strip_bold_subsections(text: str, labels: List[str]) -> str:
    """Remove bold-labeled subsections matching any label in `labels`.

    A bold subsection starts with `**<label>:**` on its own line (or at the
    start of a line) and continues until one of:
      - another bold label on its own line (e.g. `**Other:**`)
      - the next `### ` or `## ` or `# ` header
      - end of file

    Trailing blank lines immediately after a stripped subsection are also
    removed so the output stays tight.
    """
    if not labels:
        return text

    label_pattern = re.compile(
        r"^\*\*(" + "|".join(re.escape(l) for l in labels) + r"):\*\*",
        re.MULTILINE,
    )
    # Any bold label on its own line — marks end of the stripped subsection
    any_bold = re.compile(r"^\*\*[A-Z][A-Za-z ]+:\*\*", re.MULTILINE)
    header = re.compile(r"^#{1,3}\s", re.MULTILINE)

    lines = text.splitlines(keepends=True)
    result: List[str] = []
    skip = False

    for line in lines:
        stripped = line.lstrip()
        if label_pattern.match(stripped):
            skip = True
            continue
        if skip:
            # End skip on next bold label, header, or non-blank-non-indented line
            # that is itself NOT a continuation of the bold subsection content.
            if any_bold.match(stripped) or header.match(stripped):
                skip = False
                # Fall through to include this line
            else:
                continue

        if not skip:
            result.append(line)

    # Collapse 3+ consecutive blank lines to 2 (tidy output)
    joined = "".join(result)
    joined = re.sub(r"\n{3,}", "\n\n", joined)
    return joined


def strip_review_content(
    text: str,
    h2_sections: List[str],
    bold_subsections: List[str],
    h3_sections: List[str] = None,
) -> str:
    """Apply h2-section, h3-section, and bold-subsection stripping."""
    text = strip_h2_sections(text, h2_sections)
    if h3_sections:
        text = strip_h3_sections(text, h3_sections)
    text = strip_bold_subsections(text, bold_subsections)
    return text