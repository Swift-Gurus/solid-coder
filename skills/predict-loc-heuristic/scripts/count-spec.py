#!/usr/bin/env python3
"""Count ACs and screens in a spec file, apply the heuristic formula, and emit JSON.

Usage:
    count-spec.py <spec-path> <output-path>

Bands and weights are sourced from spec-driven-development/specs/README.md § Scope Metrics.
Keep this script in sync if the README changes.
"""
import json
import re
import sys
from pathlib import Path


AC_WEIGHT = 12
SCREEN_WEIGHT = 80
MINOR_THRESHOLD = 200
SEVERE_THRESHOLD = 400


def severity_for(predicted_loc: int) -> str:
    if predicted_loc > SEVERE_THRESHOLD:
        return "SEVERE"
    if predicted_loc >= MINOR_THRESHOLD:
        return "MINOR"
    return "COMPLIANT"


def parse_sections(text: str) -> dict[str, str]:
    """Split markdown into top-level sections keyed by H2 heading."""
    sections: dict[str, str] = {}
    current_key: str | None = None
    buffer: list[str] = []
    for line in text.splitlines():
        h2 = re.match(r"^##\s+(?!#)(.+?)\s*$", line)
        if h2:
            if current_key is not None:
                sections[current_key] = "\n".join(buffer)
            current_key = h2.group(1).strip()
            buffer = []
        elif current_key is not None:
            buffer.append(line)
    if current_key is not None:
        sections[current_key] = "\n".join(buffer)
    return sections


BULLET_RE = re.compile(r"^[-*+]\s+\S")


def count_acs_in_user_stories(stories_section: str) -> tuple[int, list[dict]]:
    """Count bullets under each story `### ` heading. If the section has no H3 subheadings,
    treat the whole section as a single story. Bullets accept `-`, `*`, or `+`."""
    by_story: list[dict] = []
    total = 0
    if not stories_section:
        return 0, []

    story_blocks = re.split(r"^###\s+(.+?)\s*$", stories_section, flags=re.MULTILINE)
    # split returns ["preamble", heading1, body1, heading2, body2, ...]

    if len(story_blocks) == 1:
        # No `### ` subheadings — treat the entire section as one story
        ac_count = sum(1 for line in story_blocks[0].splitlines() if BULLET_RE.match(line))
        if ac_count > 0:
            by_story.append({"story_id": "(unnamed)", "ac_count": ac_count})
            total = ac_count
        return total, by_story

    for i in range(1, len(story_blocks), 2):
        heading = story_blocks[i].strip()
        body = story_blocks[i + 1] if i + 1 < len(story_blocks) else ""
        ac_count = sum(1 for line in body.splitlines() if BULLET_RE.match(line))
        by_story.append({"story_id": heading, "ac_count": ac_count})
        total += ac_count
    return total, by_story


def count_screens(ui_section: str) -> int:
    """Count `### ` subsections OR `![]()` image links inside the UI / Mockup section."""
    if not ui_section:
        return 0
    h3_count = sum(1 for line in ui_section.splitlines() if re.match(r"^###\s+\S", line))
    image_count = len(re.findall(r"!\[[^\]]*\]\([^)]+\)", ui_section))
    detected = max(h3_count, image_count)
    if detected == 0 and ui_section.strip():
        return 1  # section exists but no structural markers — count as one screen
    return detected


def find_section(sections: dict[str, str], *names: str) -> str:
    """Return the first matching section body (case-insensitive, partial match allowed)."""
    for key, value in sections.items():
        for name in names:
            if name.lower() in key.lower():
                return value
    return ""


def main() -> int:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <spec-path> <output-path>", file=sys.stderr)
        return 2

    spec_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not spec_path.is_file():
        print(f"error: spec file not found: {spec_path}", file=sys.stderr)
        return 1

    text = spec_path.read_text(encoding="utf-8")
    sections = parse_sections(text)

    stories = find_section(sections, "User Stories", "Stories", "Scenarios")
    ui = find_section(sections, "UI / Mockup", "UI/Mockup", "Mockup", "Wireframe")

    ac_count, by_story = count_acs_in_user_stories(stories)
    screens = count_screens(ui)
    predicted_loc = ac_count * AC_WEIGHT + screens * SCREEN_WEIGHT

    output = {
        "spec_path": str(spec_path),
        "ac_count": ac_count,
        "screens": screens,
        "predicted_loc": predicted_loc,
        "formula": f"({ac_count} × {AC_WEIGHT}) + ({screens} × {SCREEN_WEIGHT}) = {predicted_loc}",
        "severity": severity_for(predicted_loc),
        "by_story": by_story,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
