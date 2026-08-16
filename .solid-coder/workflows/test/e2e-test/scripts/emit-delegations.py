"""Emits deterministic labels for live session-delegate fan-out."""

from __future__ import annotations

import json


print(json.dumps({"delegations": ["first", "second"]}))
