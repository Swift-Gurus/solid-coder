"""
solid-name: POSIXAtomicFileWriter
solid-category: service
solid-spec: [SPEC-031]
solid-description: Atomically writes content to a file, raising an error if the file already exists.
"""

from __future__ import annotations

import os
from pathlib import Path

from harness.atomic_file_writing import AtomicFileWriting


class POSIXAtomicFileWriter:

    def write_exclusive(self, path: Path, content: bytes) -> None:
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        try:
            os.write(fd, content)
        finally:
            os.close(fd)
