"""
solid-description: Provides debug logging and function call instrumentation.
solid-category: utility
solid-tags: [hook, utility]
"""

import functools
import time
from pathlib import Path
from typing import Callable, Optional, Protocol


class DebugLogging(Protocol):
    def log(self, label: str, event: str) -> None: ...


class DebugLogger:
    """Appends timestamped label/event pairs to {project_dir}/{filename}.

    Injecting project_dir_fn makes it testable without touching the filesystem.
    Never raises — all I/O errors are swallowed silently.
    """

    def __init__(self, project_dir_fn: Optional[Callable[[], Path]] = None, filename: str = "debug.log") -> None:
        self._project_dir_fn = project_dir_fn or _default_project_dir
        self._filename = filename

    def log(self, label: str, event: str) -> None:
        try:
            log_path = self._project_dir_fn() / self._filename
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a") as f:
                f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {label} {event}\n")
        except Exception:
            pass


def _default_project_dir() -> Path:
    from hook_utils import solid_coder_project_dir  # lazy — avoids circular import
    return solid_coder_project_dir()


_default_logger = DebugLogger()


def Observing(label: str, *, log_args: bool = True, logger: Optional[DebugLogger] = None):
    """Decorator: logs ENTER/EXIT/ERROR to {project_dir}/debug.log.

    Args:
        label:    Identifier written on every log line (e.g. "gate.orchestrator.run").
        log_args: When True, includes a repr of positional and keyword args on ENTER.
        logger:   Override the default logger; mainly for testing.
    """
    _logger = logger or _default_logger

    def decorator(fn: Callable):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            entry = label
            if log_args:
                parts = [repr(a)[:120] for a in args] + [f"{k}={repr(v)[:120]}" for k, v in kwargs.items()]
                entry = f"{label}({', '.join(parts)})"
            _logger.log(entry, "ENTER")
            try:
                result = fn(*args, **kwargs)
                _logger.log(label, "EXIT")
                return result
            except Exception as exc:
                _logger.log(label, f"ERROR {type(exc).__name__}: {exc}")
                raise
        return wrapper
    return decorator
