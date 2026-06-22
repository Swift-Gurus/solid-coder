"""
solid-description: Orchestrates violation reading by delegating extraction and then cleaning up the output directory.
solid-category: service
solid-tags: [hook, llm]
"""

from typing import Callable, Optional, Protocol

from violation_extractor import ViolationExtracting


class OutputReading(Protocol):
    def read_violations(self, output_dir: str, path: str) -> list: ...


class FileOutputReader:
    """Orchestrates violation reading: delegates data extraction, then cleans up.

    Single responsibility: lifecycle management — find files, delegate extraction,
    clean up. Data extraction is owned by the injected ViolationExtracting dependency.
    """

    def __init__(
        self,
        extractor: ViolationExtracting,
        path_cls: Optional[Callable] = None,
        rmtree_fn: Optional[Callable] = None,
        debug: bool = False,
    ) -> None:
        import shutil as _shutil
        from pathlib import Path
        self._extractor = extractor
        self._path_cls = path_cls or Path
        self._rmtree_fn = rmtree_fn or _shutil.rmtree
        self._debug = debug

    def read_violations(self, output_dir: str, path: str) -> list:
        dir_path = self._path_cls(output_dir)
        try:
            output_files = list(dir_path.glob("*/review-output.json"))
            if not output_files:
                raise RuntimeError(
                    f"LLM did not call submit_batch_findings — no output files in {output_dir}"
                )
            return self._extractor.extract(output_dir)
        finally:
            if not self._debug:
                self._rmtree_fn(output_dir, ignore_errors=True)
