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
When backend = "claude" and ANTHROPIC_API_KEY is not set, all checks are bypassed.
"""

from __future__ import annotations

import difflib
import os as _os
import re
import sys
from pathlib import Path
from typing import Optional, Protocol, runtime_checkable

_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

import code_health_check as health
import validate_swift_frontmatter as frontmatter
from hc_checker import HealthChecking
from hc_config import hook_exclude_patterns, llm_backend
from hook_utils import GateHandling, make_hook_gate, parse_hook_event, path_matches_pattern
from hc_violation_parser import ViolationParser

_gate = make_hook_gate()

# ---------------------------------------------------------------------------
# Low-risk edit detection
# ---------------------------------------------------------------------------

_SOLID_BLOCK_RE = re.compile(r"^\s*/\*\*\s*\n(?:[ \t]+solid-[^\n]+\n)+[ \t]*\*/\s*\Z")


class EditClassifier:
    """Classifies whether an edit is low-risk (structural-only, no logic changes)."""

    def is_frontmatter_only(self, old: str, new: str) -> bool:
        return bool(_SOLID_BLOCK_RE.match(old.strip())) and bool(_SOLID_BLOCK_RE.match(new.strip()))

    def is_reorder(self, old: str, new: str) -> bool:
        return sorted(re.findall(r'\w+', old)) == sorted(re.findall(r'\w+', new))

    def is_rename(self, old: str, new: str) -> bool:
        skeleton = lambda s: re.sub(r'\b\w+\b', 'X', s)
        return skeleton(old) == skeleton(new)

    def is_low_risk(self, old: str, new: str) -> bool:
        """Return True if the edit is structural-only and cannot introduce SOLID violations."""
        return self.is_frontmatter_only(old, new) or self.is_reorder(old, new) or self.is_rename(old, new)


_edit_classifier = EditClassifier()


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


@runtime_checkable
class FileContentReading(Protocol):
    def read_text(self, path: str) -> str: ...


# ---------------------------------------------------------------------------
# Boundary adapters
# ---------------------------------------------------------------------------

class CodeHealthCheckAdapter:
    """Boundary adapter: wraps code_health_check module to HealthChecking protocol."""

    def check(self, content: str, path: str, language: str, parent_session_id: str) -> Optional[list]:
        return health._check(content, path, language, parent_session_id)


class FrontmatterAdapter:
    """Boundary adapter: wraps validate_swift_frontmatter module to FrontmatterFixing protocol."""

    def fix(self, content: str, session_id: str, path: str) -> Optional[str]:
        return frontmatter.fix(content, parent_session_id=session_id)


class OsFileReader:
    """Reads a file's full text content from the real filesystem."""

    def read_text(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Implementations
# ---------------------------------------------------------------------------

class ContentSimulator:
    """Reads the existing file, diffs, and classifies whether the edit is low-risk."""

    def __init__(
        self,
        file_reader: FileContentReading | None = None,
        classifier: EditClassifier | None = None,
    ) -> None:
        self._reader = file_reader if file_reader is not None else OsFileReader()
        self._classifier = classifier if classifier is not None else _edit_classifier

    def simulate(self, tool_name: str, tool_input: dict) -> tuple:
        """Return (content, existing_content, is_low_risk)."""
        file_path = tool_input.get("file_path", "")
        if tool_name == "Write":
            content = tool_input.get("content", "")
            existing, low_risk = "", False
            try:
                existing = self._reader.read_text(file_path)
                old_chunk, new_chunk = _diff_chunks(existing, content)
                low_risk = self._classifier.is_low_risk(old_chunk, new_chunk) if (old_chunk or new_chunk) else True
            except OSError:
                pass
            return content, existing, low_risk

        old_string = tool_input.get("old_string", "")
        new_string = tool_input.get("new_string", "")
        replace_all = tool_input.get("replace_all", False)
        low_risk = self._classifier.is_low_risk(old_string, new_string)
        existing = ""
        try:
            existing = self._reader.read_text(file_path)
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
        _fm_key = "solid-" + "description:"
        run_frontmatter = bool(re.search(r'^\s*' + _fm_key + r'\s*\S', content, re.MULTILINE))

        if not run_health and not run_frontmatter:
            self._gate.allow()
            return

        self._gate.log(f"INVOKE {file_name}: health={run_health} frontmatter={run_frontmatter}")

        if run_health:
            try:
                violations = self._health.check(content, file_path, language, session_id)
            except Exception as exc:
                self._gate.log(f"BLOCK {file_name}: health subprocess error: {exc}")
                self._gate.block(
                    f"[health-check] Gate subprocess failed — the write is blocked.\n\n"
                    f"Error: {exc}\n\n"
                    f"Stop and report this error to the user. Do not attempt to write the file again "
                    f"until the subprocess issue is resolved."
                )
                return
            if violations:
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
            try:
                corrected = self._frontmatter.fix(content, session_id, file_path)
            except Exception as exc:
                self._gate.log(f"BLOCK {file_name}: frontmatter subprocess error: {exc}")
                self._gate.block(
                    f"[frontmatter] Gate subprocess failed — the write is blocked.\n\n"
                    f"Error: {exc}\n\n"
                    f"Stop and report this error to the user. Do not attempt to write the file again "
                    f"until the subprocess issue is resolved."
                )

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


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

class DefaultCoordinatorFactory:
    """Composition root for WriteGateCoordinator — all deps injectable, production defaults wired here."""

    def __init__(
        self,
        health_checker: HealthChecking | None = None,
        frontmatter_fixer: FrontmatterFixing | None = None,
        formatter: ViolationFormatting | None = None,
        simulator: ContentSimulating | None = None,
    ) -> None:
        self._health = health_checker if health_checker is not None else CodeHealthCheckAdapter()
        self._frontmatter = frontmatter_fixer if frontmatter_fixer is not None else FrontmatterAdapter()
        self._formatter = formatter if formatter is not None else ViolationParser()
        self._simulator = simulator if simulator is not None else ContentSimulator()

    def make(self, gate: GateHandling) -> WriteGateCoordinator:
        return WriteGateCoordinator(
            health_checker=self._health,
            frontmatter_fixer=self._frontmatter,
            formatter=self._formatter,
            simulator=self._simulator,
            gate=gate,
        )


_coordinator_factory = DefaultCoordinatorFactory()


# ---------------------------------------------------------------------------
# API key guard
# ---------------------------------------------------------------------------

def _api_key_available() -> bool:
    """Return True if the configured backend can authenticate.

    The Claude backend requires ANTHROPIC_API_KEY. The local backend (llama-server)
    does not. MAX plan users without an API key are bypassed automatically.
    """
    if llm_backend().lower() != "claude":
        return True
    return bool(_os.environ.get("ANTHROPIC_API_KEY", "").strip())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    if not _api_key_available():
        _gate.allow()
        return

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
    _coordinator_factory.make(gate=_gate).run(tool_name, tool_input, file_path, language, session_id)


if __name__ == "__main__":
    main()
