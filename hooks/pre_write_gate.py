#!/usr/bin/env python3
"""PreToolUse gate — health check first, then frontmatter correction if clean.

Flow:
  1. Health check: review code against SOLID/DRY rules.
     - Violations found  → deny immediately (no frontmatter cost wasted).
     - Clean or error    → proceed to step 2.

  2. Frontmatter correction: fix solid-description if needed.
     - Corrected         → allow with updatedInput (clean code, clean description).
     - Already clean     → allow silently.

Sequential ordering ensures:
  - Frontmatter only runs on code that passed health (correct semantic context).
  - No wasted LLM call on frontmatter when the write will be denied anyway.
  - The corrected description reflects the code that will actually be written.

Fails open on infrastructure errors in either check.
Paths matching [hooks.pre_write_gate].exclude in solid-coder-local.toml bypass all checks.
"""

import difflib
import re
import sys
from pathlib import Path
from typing import Optional, Protocol

_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

import code_health_check as health
import validate_swift_frontmatter as frontmatter
from hc_checker import HealthChecking
from hc_config import hook_exclude_patterns
from hook_callable import CallableAdapting
from hook_utils import GateHandling, make_hook_gate, parse_hook_event, path_matches_pattern
from hc_violation_parser import ViolationParser

_gate = make_hook_gate()

# ---------------------------------------------------------------------------
# Low-risk edit detection
# ---------------------------------------------------------------------------

_SOLID_BLOCK_RE = re.compile(r"^\s*/\*\*\s*\n(?:[ \t]+solid-[^\n]+\n)+[ \t]*\*/\s*\Z")


def _is_frontmatter_only(old: str, new: str) -> bool:
    return bool(_SOLID_BLOCK_RE.match(old.strip())) and bool(_SOLID_BLOCK_RE.match(new.strip()))


def _is_reorder(old: str, new: str) -> bool:
    return sorted(re.findall(r'\w+', old)) == sorted(re.findall(r'\w+', new))


def _is_rename(old: str, new: str) -> bool:
    skeleton = lambda s: re.sub(r'\b\w+\b', 'X', s)
    return skeleton(old) == skeleton(new)


def _is_low_risk_edit(old: str, new: str) -> bool:
    """Return True if the edit is structural-only and cannot introduce SOLID violations."""
    return _is_frontmatter_only(old, new) or _is_reorder(old, new) or _is_rename(old, new)


def _diff_chunks(old_content: str, new_content: str) -> tuple:
    """Return (old_changed, new_changed) — only the lines that actually changed."""
    old_lines = old_content.splitlines()
    new_lines = new_content.splitlines()
    old_changed, new_changed = [], []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old_lines, new_lines).get_opcodes():
        if tag == "equal":
            continue
        old_changed.extend(old_lines[i1:i2])
        new_changed.extend(new_lines[j1:j2])
    return "\n".join(old_changed), "\n".join(new_changed)


# ---------------------------------------------------------------------------
# Protocols
# ---------------------------------------------------------------------------

class FrontmatterFixing(Protocol):
    def fix(self, content: str, session_id: str, path: str) -> Optional[str]: ...


class ViolationFormatting(Protocol):
    def format_block_reason(self, violations: list) -> str: ...


class ContentSimulating(Protocol):
    def simulate(self, tool_name: str, tool_input: dict) -> tuple: ...


# ---------------------------------------------------------------------------
# Concrete implementations
# ---------------------------------------------------------------------------

class HealthChecker(CallableAdapting):
    """Callable adapter for code_health_check._check."""

    def check(self, content: str, path: str, language: str, parent_session_id: str) -> Optional[list]:
        return self._safe_call(content, path, language, parent_session_id)


class FrontmatterFixer(CallableAdapting):
    """Callable adapter for validate_swift_frontmatter.fix_with_claude."""

    def fix(self, content: str, session_id: str, path: str) -> Optional[str]:
        return self._safe_call(content, parent_session_id=session_id)


class ContentSimulator:
    """Reads the existing file, diffs, and classifies whether the edit is low-risk."""

    def simulate(self, tool_name: str, tool_input: dict) -> tuple:
        """Return (content, existing_content, is_low_risk)."""
        file_path = tool_input.get("file_path", "")
        if tool_name == "Write":
            content = tool_input.get("content", "")
            existing, low_risk = "", False
            try:
                existing = Path(file_path).read_text(encoding="utf-8")
                old_chunk, new_chunk = _diff_chunks(existing, content)
                low_risk = _is_low_risk_edit(old_chunk, new_chunk) if (old_chunk or new_chunk) else True
            except OSError:
                pass
            return content, existing, low_risk

        old_string = tool_input.get("old_string", "")
        new_string = tool_input.get("new_string", "")
        replace_all = tool_input.get("replace_all", False)
        low_risk = _is_low_risk_edit(old_string, new_string)
        existing = ""
        try:
            existing = Path(file_path).read_text(encoding="utf-8")
            content = existing.replace(old_string, new_string) if replace_all \
                      else existing.replace(old_string, new_string, 1)
        except OSError:
            content = new_string
        return content, existing, low_risk


# ---------------------------------------------------------------------------
# Exclusion
# ---------------------------------------------------------------------------

def _is_excluded_path(file_path: str) -> bool:
    """Return True if file_path matches any pre_write_gate exclusion pattern."""
    patterns = hook_exclude_patterns("pre_write_gate")
    return any(path_matches_pattern(file_path, pat) for pat in patterns)


# ---------------------------------------------------------------------------
# Coordinator
# ---------------------------------------------------------------------------

class WriteGateCoordinator:
    """Sequences health check and frontmatter correction for a single write event."""

    def __init__(
        self,
        health_checker: HealthChecking,
        frontmatter_fixer: FrontmatterFixing,
        formatter: ViolationFormatting,
        simulator: ContentSimulating,
        gate: GateHandling,
    ) -> None:
        self._health = health_checker
        self._frontmatter = frontmatter_fixer
        self._formatter = formatter
        self._simulator = simulator
        self._gate = gate

    def run(
        self,
        tool_name: str,
        tool_input: dict,
        file_path: str,
        language: str,
        session_id: str,
    ) -> None:
        content, existing, low_risk = self._simulator.simulate(tool_name, tool_input)
        file_name = Path(file_path).name

        run_health = not low_risk
        run_frontmatter = "solid-description:" in content

        if not run_health and not run_frontmatter:
            self._gate.allow()
            return

        self._gate.log(f"INVOKE {file_name}: health={run_health} frontmatter={run_frontmatter}")

        if run_health:
            violations = self._health.check(content, file_path, language, session_id)
            if violations is None:
                self._gate.log(f"FAILOPEN {file_name}: health check returned None (subprocess error)")
            elif violations:
                self._gate.log(f"DENY {file_name}: {len(violations)} violation(s)")
                parts = [
                    self._formatter.format_block_reason(violations),
                    "The file was NOT written. You MUST fix all violations above "
                    "and write the corrected version before continuing.",
                ]
                self._gate.block("[health-check] " + "\n\n".join(parts))
                return

        corrected = None
        if run_frontmatter:
            corrected = self._frontmatter.fix(content, session_id, file_path)

        if corrected is not None and corrected != content:
            self._gate.log(f"CORRECTED {file_name}: frontmatter updated")
            updated = dict(tool_input)
            if tool_name == "Write":
                updated["content"] = corrected
            elif existing:
                updated["old_string"] = existing
                updated["new_string"] = corrected
                updated.pop("replace_all", None)
            else:
                updated["new_string"] = corrected
            self._gate.allow_with_update(updated)
        else:
            if run_health or run_frontmatter:
                self._gate.log(f"CLEAN {file_name}")
            self._gate.allow()


def _make_coordinator(gate: GateHandling) -> WriteGateCoordinator:
    return WriteGateCoordinator(
        health_checker=HealthChecker(fn=health._check),
        frontmatter_fixer=FrontmatterFixer(fn=frontmatter.fix),
        formatter=ViolationParser(),
        simulator=ContentSimulator(),
        gate=gate,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parsed = parse_hook_event(sys.stdin.read())
    if parsed is None:
        _gate.allow()
        return

    tool_name, tool_input, file_path, session_id = parsed

    ext = Path(file_path).suffix.lower()
    if ext not in health.SUPPORTED_EXTENSIONS:
        _gate.allow()
        return

    if _is_excluded_path(file_path):
        _gate.allow()
        return

    if tool_name not in ("Write", "Edit"):
        _gate.allow()
        return

    language = health.SUPPORTED_EXTENSIONS[ext]
    _make_coordinator(gate=_gate).run(tool_name, tool_input, file_path, language, session_id)


if __name__ == "__main__":
    main()
