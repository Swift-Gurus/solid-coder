"""
solid-description: Gates source file modifications based on code quality standards.
solid-category: service
solid-tags: [hook]
"""

import json
import sys
from pathlib import Path
from typing import Optional, Protocol

_HOOKS_DIR = Path(__file__).resolve().parents[1]
_PATCH_DIR = Path(__file__).resolve().parent
for _d in (_HOOKS_DIR, _PATCH_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from hook_utils import GateHandling, HookGateFactory


# ── Protocols ─────────────────────────────────────────────────────────────────

class HealthChecking(Protocol):
    def check(self, content: str, path: str, language: str, session_id: str) -> Optional[list]: ...


class ViolationFormatting(Protocol):
    def format_block_reason(self, violations: list) -> str: ...


class PatchExtracting(Protocol):
    def extract(self, entry: dict) -> tuple: ...


class PatchParsing(Protocol):
    def parse(self, command: str) -> list: ...
    def add_content(self, lines: list) -> str: ...
    def apply_update(self, existing_content: str, body_lines: list) -> str: ...


# ── Content extraction ────────────────────────────────────────────────────────

class PatchContentExtractor:
    """Extracts post-apply file content from a parsed patch entry."""

    def __init__(self, parser: PatchParsing) -> None:
        self._parser = parser

    def extract(self, entry: dict) -> tuple:
        if entry["operation"] == "add":
            return entry["path"], self._parser.add_content(entry["lines"])
        try:
            existing = Path(entry["path"]).read_text(encoding="utf-8")
            return entry["path"], self._parser.apply_update(existing, entry["lines"])
        except OSError:
            return entry["path"], ""


# ── Gate coordinator ──────────────────────────────────────────────────────────

class ApplyPatchGate:
    """Coordinates health checks for each source file touched by an apply_patch command."""

    def __init__(
        self,
        gate: GateHandling,
        checker: HealthChecking,
        formatter: ViolationFormatting,
        extractor: PatchExtracting,
        parser: PatchParsing,
        supported_extensions: dict,
    ) -> None:
        self._gate = gate
        self._checker = checker
        self._formatter = formatter
        self._extractor = extractor
        self._parser = parser
        self._supported = supported_extensions

    def run(self, event: dict) -> None:
        tool_input = event.get("tool_input") or {}
        session_id = event.get("session_id", "")
        entries = [
            e for e in self._parser.parse(tool_input.get("command", ""))
            if e["operation"] != "delete"
            and Path(e["path"]).suffix.lower() in self._supported
        ]
        if not entries:
            self._gate.allow()
            return
        for entry in entries:
            file_path, content = self._extractor.extract(entry)
            if not content:
                continue
            language = self._supported[Path(file_path).suffix.lower()]
            try:
                violations = self._checker.check(content, file_path, language, session_id)
            except Exception as exc:
                self._gate.block(f"[health-check] Gate subprocess failed for {file_path}:\n{exc}")
                return
            if violations:
                reason = self._formatter.format_block_reason(violations)
                self._gate.block(
                    "[health-check] " + reason
                    + "\n\nFix all violations before writing."
                )
                return
        self._gate.allow()


# ── Health check adapter ──────────────────────────────────────────────────────

class HealthCheckAdapter:
    """Boundary adapter: wraps code_health_check._check to the HealthChecking protocol."""

    def check(self, content: str, path: str, language: str, session_id: str) -> Optional[list]:
        from code_health_check import _check
        return _check(content, path, language, session_id)


# ── Composition root ──────────────────────────────────────────────────────────

def _build_gate(raw: str):
    from code_health_check import SUPPORTED_EXTENSIONS
    from hc_violation_parser import ViolationParser
    from apply_patch_parser import ApplyPatchParser
    from patch_format_parser import PatchFormatParser
    from add_content_extractor import AddContentExtractor
    from hunk_applicator import HunkApplicator
    gate = HookGateFactory().build()
    try:
        event = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        gate.allow()
        return None
    if event.get("tool_name") != "apply_patch":
        gate.allow()
        return None
    parser = ApplyPatchParser(
        format_parser=PatchFormatParser(),
        content_extractor=AddContentExtractor(),
        hunk_applicator=HunkApplicator(),
    )
    return ApplyPatchGate(
        gate=gate,
        checker=HealthCheckAdapter(),
        formatter=ViolationParser(),
        extractor=PatchContentExtractor(parser=parser),
        parser=parser,
        supported_extensions=SUPPORTED_EXTENSIONS,
    ), event


def main() -> None:
    raw = sys.stdin.read()
    built = _build_gate(raw)
    if built is None:
        return
    gate_obj, event = built
    gate_obj.run(event)


if __name__ == "__main__":
    main()
