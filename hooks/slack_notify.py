#!/usr/bin/env python3
"""
solid-description: Notifies via webhook when Claude stops or requests tool permission.
solid-category: hook

To enable:
    export CLAUDE_SLACK_NOTIFY=https://hooks.slack.com/services/T.../B/.../...

The webhook URL is self-authenticating — no OAuth or tokens required.
Create one at api.slack.com/apps > Incoming Webhooks, select yourself
as the destination to receive it as a DM.

Threshold:
    Set [slack] task_length_threshold in solid-coder-local.toml to only
    notify when the task took longer than N seconds. 0 = always notify.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Protocol, runtime_checkable

from hc_llama_runner import HttpSending, UrllibSender

_MAX_LAST_MESSAGE_LEN = 500
_SLACK_HEADERS = {"Content-Type": "application/json"}
_SLACK_TIMEOUT = 3
_COMMAND_MESSAGE_RE = re.compile(r"<command-message>(.*?)</command-message>", re.DOTALL)

_MODE_ICONS: dict[str, str] = {
    "review": ":mag:",
    "implement": ":hammer_and_wrench:",
    "refactor": ":recycle:",
    "vibe": ":magic_wand:",
}


def _normalize_content_text(content) -> str:
    """Normalize a message content field to plain text regardless of its type."""
    if isinstance(content, str):
        return content
    if isinstance(content, list) and content and isinstance(content[0], dict):
        return content[0].get("text", "")
    return ""


# ---------------------------------------------------------------------------
# Infrastructure protocols + adapters
# ---------------------------------------------------------------------------

@runtime_checkable
class EnvironmentReading(Protocol):
    def get(self, key: str, default: str = "") -> str: ...


class OSEnvironmentAdapter:
    """Wraps an environment mapping; defaults to os.environ at construction time."""

    def __init__(self, environ: dict = os.environ) -> None:
        self._environ = environ

    def get(self, key: str, default: str = "") -> str:
        return self._environ.get(key, default)


@runtime_checkable
class FileLineReading(Protocol):
    def read_lines(self, path: str) -> list: ...


class FileSystemLineReader:
    """Reads lines from the real filesystem."""

    def read_lines(self, path: str) -> list:
        try:
            with open(path, encoding="utf-8") as f:
                return f.readlines()
        except OSError:
            return []


@runtime_checkable
class JSONLParsing(Protocol):
    def messages(self, path: str) -> list: ...


class JSONLTranscriptParser:
    """Parses a JSONL transcript into a list of message dicts, skipping malformed lines."""

    def __init__(self, file_reader: FileLineReading) -> None:
        self._reader = file_reader

    def messages(self, path: str) -> list:
        result = []
        for line in self._reader.read_lines(path):
            try:
                result.append(json.loads(line.strip()))
            except (json.JSONDecodeError, ValueError):
                pass
        return result


@runtime_checkable
class PathNaming(Protocol):
    def name(self, path: str) -> str: ...


class PathLibNamer:
    """Extracts the final component of a path via pathlib."""

    def name(self, path: str) -> str:
        return Path(path).name if path else ""


@runtime_checkable
class ClockReading(Protocol):
    def now_utc(self) -> datetime: ...


class SystemClock:
    """Returns the real current UTC time."""

    def now_utc(self) -> datetime:
        return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Domain protocols
# ---------------------------------------------------------------------------

@runtime_checkable
class ConfigReading(Protocol):
    def webhook_url(self) -> str: ...
    def is_enabled(self) -> bool: ...


@runtime_checkable
class ThresholdReading(Protocol):
    def threshold_seconds(self) -> int: ...


@runtime_checkable
class AssistantTextReading(Protocol):
    def last_assistant_text(self) -> str: ...


@runtime_checkable
class SkillCallsReading(Protocol):
    def skill_calls(self) -> list: ...


@runtime_checkable
class TranscriptReading(Protocol):
    def last_assistant_text(self) -> str: ...
    def skill_calls(self) -> list: ...


@runtime_checkable
class ElapsedTimeReading(Protocol):
    def elapsed_seconds(self, transcript_path: str) -> float: ...


@runtime_checkable
class ModeClassifying(Protocol):
    def classify(self, skill_calls: list) -> str: ...


@runtime_checkable
class PayloadBuilding(Protocol):
    def build(self) -> dict: ...


@runtime_checkable
class WebhookSending(Protocol):
    def send(self, payload: dict) -> None: ...


# ---------------------------------------------------------------------------
# Implementations
# ---------------------------------------------------------------------------

class EnvConfigReader:
    """Reads the Slack webhook URL from the CLAUDE_SLACK_NOTIFY environment variable."""

    ENV_VAR = "CLAUDE_SLACK_NOTIFY"

    def __init__(self, env: EnvironmentReading | None = None) -> None:
        self._env = env if env is not None else OSEnvironmentAdapter()

    def webhook_url(self) -> str:
        return self._env.get(self.ENV_VAR, "").strip()

    def is_enabled(self) -> bool:
        return bool(self.webhook_url())


class TomlThresholdReader:
    """Reads task_length_threshold from the [slack] section of solid-coder-local.toml."""

    def __init__(self, threshold_fn: Callable[[], int] | None = None) -> None:
        if threshold_fn is None:
            from hc_config_core import read_section, safe_convert  # noqa: PLC0415
            def _default() -> int:
                return safe_convert(
                    read_section("slack").get("task_length_threshold"), 60, int
                )
            threshold_fn = _default
        self._fn = threshold_fn

    def threshold_seconds(self) -> int:
        return self._fn()


class AssistantTextReader:
    """Reads the last non-empty text block from the last assistant message."""

    def __init__(self, transcript_path: str, parser: JSONLParsing) -> None:
        self._path = transcript_path
        self._parser = parser

    def last_assistant_text(self) -> str:
        last_text = ""
        for obj in self._parser.messages(self._path):
            if obj.get("type") == "assistant":
                for block in obj.get("message", {}).get("content", []):
                    if block.get("type") == "text":
                        text = block.get("text", "").strip()
                        if text:
                            last_text = text
        return last_text


class SkillCallsReader:
    """Extracts invoked skill names from a Claude Code JSONL transcript.

    Strategy (in order):
    1. Parse <command-message> from the first user message (main session format).
    2. Fall back to scanning assistant Skill tool_use blocks (subagent format).
    """

    def __init__(self, transcript_path: str, parser: JSONLParsing) -> None:
        self._path = transcript_path
        self._parser = parser

    def skill_calls(self) -> list:
        messages = self._parser.messages(self._path)
        command = self._command_from_user_message(messages)
        if command:
            return [command]
        return self._skills_from_tool_use(messages)

    def _command_from_user_message(self, messages: list) -> str:
        for obj in messages:
            if obj.get("type") == "user":
                text = _normalize_content_text(obj.get("message", {}).get("content", ""))
                match = _COMMAND_MESSAGE_RE.search(text)
                return match.group(1).strip() if match else ""
        return ""

    def _skills_from_tool_use(self, messages: list) -> list:
        skills: list[str] = []
        for obj in messages:
            if obj.get("type") == "assistant":
                for block in obj.get("message", {}).get("content", []):
                    if (
                        block.get("type") == "tool_use"
                        and block.get("name") == "Skill"
                    ):
                        skill = (block.get("input") or {}).get("skill", "")
                        if skill:
                            skills.append(skill)
        return skills


class TranscriptReader:
    """Facade: delegates text and skill-call extraction to focused readers."""

    def __init__(
        self,
        transcript_path: str,
        file_reader: FileLineReading | None = None,
        text_reader: AssistantTextReading | None = None,
        skills_reader: SkillCallsReading | None = None,
    ) -> None:
        fr = file_reader if file_reader is not None else FileSystemLineReader()
        parser = JSONLTranscriptParser(fr)
        self._text_reader = text_reader or AssistantTextReader(transcript_path, parser)
        self._skills_reader = skills_reader or SkillCallsReader(transcript_path, parser)

    def last_assistant_text(self) -> str:
        return self._text_reader.last_assistant_text()

    def skill_calls(self) -> list:
        return self._skills_reader.skill_calls()


class TranscriptElapsedReader:
    """Computes seconds elapsed since the last user message in the transcript."""

    def __init__(
        self,
        file_reader: FileLineReading | None = None,
        clock: ClockReading | None = None,
    ) -> None:
        fr = file_reader if file_reader is not None else FileSystemLineReader()
        self._parser = JSONLTranscriptParser(fr)
        self._clock = clock if clock is not None else SystemClock()

    def elapsed_seconds(self, transcript_path: str) -> float:
        last_ts: datetime | None = None
        for obj in self._parser.messages(transcript_path):
            if obj.get("type") == "user":
                # Skip tool_result messages — they have timestamps seconds before Stop
                # and would make elapsed appear tiny even after a long task.
                # Only track human-typed messages (text content).
                content = obj.get("message", {}).get("content", "")
                if isinstance(content, list) and content and content[0].get("type") == "tool_result":
                    continue
                raw = obj.get("timestamp", "")
                if raw:
                    try:
                        last_ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                    except ValueError:
                        pass
        if last_ts is None:
            return float("inf")
        return (self._clock.now_utc() - last_ts).total_seconds()


class ModeClassifier:
    """Classifies the session mode from skill calls."""

    _TRIGGERS: list[tuple[str, str]] = [
        ("review", "solid-coder:review"),
        ("implement", "solid-coder:implement"),
        ("refactor", "solid-coder:refactor"),
    ]

    def classify(self, skill_calls: list) -> str:
        """Return 'review', 'implement', 'refactor', or 'vibe' (default)."""
        for mode, trigger in self._TRIGGERS:
            if any(s.startswith(trigger) for s in skill_calls):
                return mode
        return "vibe"


class SlackPayloadBuilder:
    """Constructs a Slack Block Kit message payload from a Stop event dict."""

    def __init__(
        self,
        event: dict,
        mode: str = "vibe",
        last_message: str = "",
        path_namer: PathNaming | None = None,
    ) -> None:
        self._event = event
        self._mode = mode
        self._last_message = last_message
        self._path_namer = path_namer if path_namer is not None else PathLibNamer()

    def build(self) -> dict:
        cwd = self._event.get("cwd", "")
        project_name = self._path_namer.name(cwd)
        icon = _MODE_ICONS.get(self._mode, ":magic_wand:")
        first_line = self._last_message.split("\n")[0].strip() if self._last_message else ""
        header_text = f"{icon}  {first_line or 'Finished'}"

        blocks: list[dict] = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": header_text},
            }
        ]

        context_elements: list[dict] = []
        if project_name:
            context_elements.append(
                {"type": "mrkdwn", "text": f"*Project:* {project_name}"}
            )
        if cwd:
            context_elements.append(
                {"type": "mrkdwn", "text": f"*Path:* `{cwd}`"}
            )

        if context_elements:
            blocks.append({"type": "context", "elements": context_elements})

        if self._last_message:
            msg = self._last_message
            if len(msg) > _MAX_LAST_MESSAGE_LEN:
                msg = msg[:_MAX_LAST_MESSAGE_LEN] + "…"
            blocks.append({"type": "divider"})
            blocks.append(
                {"type": "section", "text": {"type": "mrkdwn", "text": msg}}
            )

        return {"text": first_line or "Finished", "blocks": blocks}


class WebhookDispatcher:
    """POSTs a Slack payload to a single webhook URL. Errors go to stderr, never raised."""

    def __init__(
        self,
        webhook_url: str,
        http_sender: HttpSending | None = None,
    ) -> None:
        self._url = webhook_url
        self._sender = http_sender if http_sender is not None else UrllibSender()

    def send(self, payload: dict) -> None:
        try:
            data = json.dumps(payload).encode("utf-8")
            self._sender.send(self._url, data, _SLACK_HEADERS, _SLACK_TIMEOUT)
        except urllib.error.HTTPError as exc:
            sys.stderr.write(f"slack_notify: HTTP {exc.code}\n")
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write(f"slack_notify: {exc}\n")


class SlackStopNotifier:
    """StopHandler implementation — sends a Slack DM when CLAUDE_SLACK_NOTIFY is set."""

    def __init__(
        self,
        config: ConfigReading | None = None,
        transcript_reader_factory: Callable[[str], TranscriptReading] | None = None,
        mode_classifier: ModeClassifying | None = None,
        payload_builder_factory: Callable[[dict, str, str], PayloadBuilding] | None = None,
        dispatcher_factory: Callable[[str], WebhookSending] | None = None,
        threshold_reader: ThresholdReading | None = None,
        elapsed_reader: ElapsedTimeReading | None = None,
    ) -> None:
        self._config = config if config is not None else EnvConfigReader()
        self._reader_factory = transcript_reader_factory or TranscriptReader
        self._classifier = mode_classifier if mode_classifier is not None else ModeClassifier()
        self._builder_factory = payload_builder_factory or SlackPayloadBuilder
        self._dispatcher_factory = dispatcher_factory or WebhookDispatcher
        self._threshold = threshold_reader if threshold_reader is not None else TomlThresholdReader()
        self._elapsed = elapsed_reader if elapsed_reader is not None else TranscriptElapsedReader()

    def should_handle(self, event: dict) -> bool:
        if not self._config.is_enabled():
            return False
        threshold = self._threshold.threshold_seconds()
        if threshold > 0:
            elapsed = self._elapsed.elapsed_seconds(event.get("transcript_path", ""))
            if elapsed < threshold:
                return False
        return True

    def handle(self, event: dict) -> None:
        transcript_path = event.get("transcript_path", "")
        mode = "vibe"
        last_message = ""
        if transcript_path:
            reader = self._reader_factory(transcript_path)
            mode = self._classifier.classify(reader.skill_calls())
            last_message = reader.last_assistant_text()
        payload = self._builder_factory(event, mode, last_message).build()
        self._dispatcher_factory(self._config.webhook_url()).send(payload)


# ---------------------------------------------------------------------------
# Permission request notification
# ---------------------------------------------------------------------------

_TOOL_ICONS: dict[str, str] = {
    "Write": ":pencil2:",
    "Edit": ":pencil2:",
    "Bash": ":computer:",
    "Read": ":open_book:",
    "WebFetch": ":globe_with_meridians:",
    "WebSearch": ":mag:",
    "Glob": ":file_folder:",
    "Grep": ":mag_right:",
}

_TOOL_ICON_DEFAULT = ":key:"


def _summarise_tool_input(tool_name: str, tool_input: dict) -> str:
    """Return a short human-readable summary of a tool's input."""
    if tool_name in ("Write", "Edit", "Read"):
        return tool_input.get("file_path", "")
    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
        return cmd[:120] + ("…" if len(cmd) > 120 else "")
    if tool_name in ("WebFetch", "WebSearch"):
        return tool_input.get("url", tool_input.get("query", ""))
    if tool_name in ("Glob", "Grep"):
        return tool_input.get("pattern", tool_input.get("query", ""))
    for v in tool_input.values():
        if isinstance(v, str) and v:
            return v[:120]
    return ""


class PermissionPayloadBuilder:
    """Builds a Slack Block Kit payload for a PermissionRequest event."""

    def __init__(self, event: dict, path_namer: PathNaming | None = None) -> None:
        self._event = event
        self._path_namer = path_namer if path_namer is not None else PathLibNamer()

    def build(self) -> dict:
        tool_name = self._event.get("tool_name", "Unknown")
        tool_input = self._event.get("tool_input") or {}
        cwd = self._event.get("cwd", "")
        project_name = self._path_namer.name(cwd)

        icon = _TOOL_ICONS.get(tool_name, _TOOL_ICON_DEFAULT)
        summary = _summarise_tool_input(tool_name, tool_input)
        header_text = f"{icon}  Permission needed — `{tool_name}`"

        blocks: list[dict] = [
            {"type": "section", "text": {"type": "mrkdwn", "text": header_text}},
        ]

        context_elements: list[dict] = []
        if project_name:
            context_elements.append({"type": "mrkdwn", "text": f"*Project:* {project_name}"})
        if summary:
            context_elements.append({"type": "mrkdwn", "text": f"`{summary}`"})
        if context_elements:
            blocks.append({"type": "context", "elements": context_elements})

        return {"text": f"Permission needed — {tool_name}", "blocks": blocks}


class SlackPermissionNotifier:
    """Sends a Slack notification when Claude Code requests tool permission."""

    def __init__(
        self,
        config: ConfigReading | None = None,
        payload_builder_factory: Callable[[dict], PayloadBuilding] | None = None,
        dispatcher_factory: Callable[[str], WebhookSending] | None = None,
    ) -> None:
        self._config = config if config is not None else EnvConfigReader()
        self._builder_factory = payload_builder_factory or PermissionPayloadBuilder
        self._dispatcher_factory = dispatcher_factory or WebhookDispatcher

    def should_handle(self, event: dict) -> bool:
        return self._config.is_enabled()

    def handle(self, event: dict) -> None:
        payload = self._builder_factory(event).build()
        self._dispatcher_factory(self._config.webhook_url()).send(payload)
