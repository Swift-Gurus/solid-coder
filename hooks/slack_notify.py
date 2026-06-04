#!/usr/bin/env python3
"""
solid-description: Sends a Slack notification when a stop event occurs.
solid-category: hook

To enable:
    export CLAUDE_SLACK_NOTIFY=https://hooks.slack.com/services/T.../B/.../...

The webhook URL is self-authenticating — no OAuth or tokens required.
Create one at api.slack.com/apps > Incoming Webhooks, select yourself
as the destination to receive it as a DM.

To add more channels in the future, extend CLAUDE_SLACK_NOTIFY to a
comma-separated list of URLs or introduce a config file — this module
is the only place that needs to change.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


class EnvConfigReader:
    """Reads the Slack webhook URL from the CLAUDE_SLACK_NOTIFY environment variable."""

    ENV_VAR = "CLAUDE_SLACK_NOTIFY"

    def webhook_url(self) -> str:
        return os.environ.get(self.ENV_VAR, "").strip()

    def is_enabled(self) -> bool:
        return bool(self.webhook_url())


class SlackPayloadBuilder:
    """Constructs a Slack Block Kit message payload from a Stop event dict."""

    def __init__(self, event: dict) -> None:
        self._event = event

    def build(self) -> dict:
        cwd = self._event.get("cwd", "")
        project_name = Path(cwd).name if cwd else ""
        header_text = ":robot_face:  Claude finished — Waiting for your input"

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

        return {"text": header_text, "blocks": blocks}


class WebhookDispatcher:
    """POSTs a Slack payload to a single webhook URL. Errors go to stderr, never raised."""

    def __init__(self, webhook_url: str) -> None:
        self._url = webhook_url

    def send(self, payload: dict) -> None:
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self._url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=3):
                pass
        except urllib.error.HTTPError as exc:
            sys.stderr.write(f"slack_notify: HTTP {exc.code}\n")
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write(f"slack_notify: {exc}\n")


class SlackStopNotifier:
    """StopHandler implementation — sends a Slack DM when CLAUDE_SLACK_NOTIFY is set."""

    def __init__(self) -> None:
        self._config = EnvConfigReader()

    def should_handle(self, event: dict) -> bool:
        return self._config.is_enabled()

    def handle(self, event: dict) -> None:
        payload = SlackPayloadBuilder(event).build()
        WebhookDispatcher(self._config.webhook_url()).send(payload)
