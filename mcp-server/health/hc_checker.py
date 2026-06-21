"""
solid-description: Analyzes source code for code health violations.
solid-category: service
solid-tags: [hook, llm]
"""

import sys
from pathlib import Path
from typing import Optional, Protocol

_HEALTH_DIR = Path(__file__).resolve().parent
_HOOKS_DIR = _HEALTH_DIR.parents[1] / 'hooks'
for _d in (_HOOKS_DIR, _HEALTH_DIR, _HEALTH_DIR / "config", _HEALTH_DIR / "llm", _HEALTH_DIR / "codex"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

# Re-exports for backwards compatibility
from claude_runner import ClaudeRunning, ClaudeRunner, ClaudeCallable  # noqa: F401
from principles_loader import PrinciplesLoading, PrinciplesLoader  # noqa: F401
from health_prompt_builder import PromptBuilding, HealthPromptBuilder  # noqa: F401
from llm_executor import LLMExecuting, LLMExecutor  # noqa: F401
from path_file_system_reader import FileSystemReading, PathFileSystemReader  # noqa: F401
from violation_extractor import ViolationExtracting, ViolationExtractor  # noqa: F401
from file_output_reader import OutputReading, FileOutputReader  # noqa: F401
from response_parser import ResponseParsing, ResponseParser  # noqa: F401
from file_based_output_handler import OutputHandling, FileBasedOutputHandler  # noqa: F401
from text_based_output_handler import TextBasedOutputHandler  # noqa: F401
from llm_reviewer import LLMReviewing, LLMReviewer  # noqa: F401
from output_path_resolver import OutputPathResolving, SessionOutputPathResolver  # noqa: F401
from health_check_context_writing import HealthCheckContextWriting  # noqa: F401


class HealthChecking(Protocol):
    def check(
        self,
        content: str,
        path: str,
        language: str,
        parent_session_id: str,
    ) -> Optional[list]: ...


class LLMHealthChecker:
    """Facade coordinating principle loading, prompt building, and LLM review."""

    def __init__(
        self,
        loader: PrinciplesLoading,
        builder: PromptBuilding,
        reviewer: LLMReviewing,
        path_resolver: OutputPathResolving,
        context_writer: Optional[HealthCheckContextWriting] = None,
    ) -> None:
        self._loader = loader
        self._builder = builder
        self._reviewer = reviewer
        self._path_resolver = path_resolver
        self._context_writer = context_writer

    def check(
        self,
        content: str,
        path: str,
        language: str,
        parent_session_id: str,
    ) -> Optional[list]:
        principles = self._loader.load(content, path)
        if principles is None:
            return None
        if not principles:
            return []
        output_dir = self._path_resolver.resolve(parent_session_id)
        if self._context_writer is not None:
            self._context_writer.write(output_dir, path, language, content)
        prompt = self._builder.build(principles, content, path, parent_session_id, output_dir)
        return self._reviewer.review(prompt, path, output_dir=output_dir)
