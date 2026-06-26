"""
solid-description: Serializes and records events to files.
solid-category: service
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Protocol


class EventSerializing(Protocol):
    """
    solid-description: Contract for serializing an event to a string.
    solid-category: abstraction
    """

    def serialize(self, event_type: str, payload: dict[str, Any]) -> str: ...


class FileLineAppending(Protocol):
    """
    solid-description: Contract for appending lines to a file.
    solid-category: abstraction
    """

    def append_line(self, path: str, line: str) -> None: ...


class EventAppending(Protocol):
    """
    solid-description: Contract for appending events.
    solid-category: abstraction
    """

    def append(self, path: str, event_type: str, payload: dict[str, Any]) -> None: ...


class EventSerializer:
    """
    solid-description: Serializes events to strings.
    solid-category: service
    """

    def serialize(self, event_type: str, payload: dict[str, Any]) -> str:
        record: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
        }
        record.update(payload)
        return json.dumps(record, default=str)


class POSIXFileAppender:
    """
    solid-description: Appends lines to files.
    solid-category: service
    """

    def append_line(self, path: str, line: str) -> None:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        try:
            os.write(fd, (line + "\n").encode())
        finally:
            os.close(fd)


class EventAppender:
    """
    solid-description: Records events to files.
    solid-category: service
    """

    def __init__(self, serializer: EventSerializing, file_appender: FileLineAppending) -> None:
        self._serializer = serializer
        self._file_appender = file_appender

    def append(self, path: str, event_type: str, payload: dict[str, Any]) -> None:
        line = self._serializer.serialize(event_type, payload)
        self._file_appender.append_line(path, line)
