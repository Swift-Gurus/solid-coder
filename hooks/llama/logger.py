"""
solid-description: Logs structured events for each phase of a local LLM session.
solid-category: service
solid-tags: [hook, llm]
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from llama.log_entry_writer import LogEntryWriting, JsonlEntryWriter
from llama.timer import TimeMeasuring, MonotonicTimer
from llama.directory_creator import DirectoryCreating, PathDirectoryCreator


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _summarise_result(name: str, result_str: str) -> dict:
    if name == "mcp__plugin_solid-coder_pipeline__search_codebase":
        return {"hits": result_str.count(" — ")}
    if name == "mcp__plugin_solid-coder_docs__load_fix_for_violation":
        return {"content_len": len(result_str)}
    return {"len": len(result_str)}


class LocalLLMLogger:
    """Writes per-tool-call JSONL entries to a caller-supplied log directory."""

    def __init__(
        self,
        log_dir: Path,
        file_path: str,
        model: str,
        entry_writer: Optional[LogEntryWriting] = None,
        timer: Optional[TimeMeasuring] = None,
        dir_creator: Optional[DirectoryCreating] = None,
    ) -> None:
        _creator: DirectoryCreating = dir_creator or PathDirectoryCreator()
        _creator.create(log_dir)
        self._dir = log_dir
        self._file = Path(file_path).name
        self._model = model
        self._writer: LogEntryWriting = entry_writer or JsonlEntryWriter()
        self._timer: TimeMeasuring = timer or MonotonicTimer()
        self._t0 = self._timer.now()

    def _write(self, filename: str, entry: dict) -> None:
        entry.setdefault("ts", _now())
        self._writer.append(self._dir, filename, entry)

    def log_start(self, prompt_len: int) -> None:
        self._write("_exchange.jsonl", {
            "ev": "start", "file": self._file,
            "model": self._model, "prompt_len": prompt_len,
        })

    def log_tool_call(self, call_id: str, name: str, args: dict) -> None:
        self._write(f"{call_id}.jsonl", {"ev": "call", "name": name, "args": args})

    def log_tool_result(self, call_id: str, name: str, result_str: str) -> None:
        summary = _summarise_result(name, result_str)
        self._write(f"{call_id}.jsonl", {"ev": "result", **summary})

    def log_thinking(self, round: int, content: str) -> None:
        self._write("_thinking.jsonl", {
            "ev": "thinking", "round": round, "file": self._file, "content": content,
        })

    def log_done(self, rounds: int, usage: dict, violations: list, thinking: str = "") -> None:
        elapsed_ms = int(self._timer.elapsed(self._t0) * 1000)
        entry: dict = {
            "ev": "done",
            "rounds": rounds,
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "elapsed_ms": elapsed_ms,
            "result": "blocked" if violations else "clean",
            "violations": violations,
        }
        if thinking:
            entry["thinking_len"] = len(thinking)
            self._write("_thinking.jsonl", {"ev": "thinking", "file": self._file, "content": thinking})
        self._write("_exchange.jsonl", entry)
