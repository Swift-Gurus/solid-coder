"""Decodes inbound JSON-RPC envelopes before transport routing."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, JsonValue

"""
solid-name: RpcInboundMessage
solid-category: model
solid-spec: [SPEC-064]
solid-description: Represents inbound protocol envelopes while retaining the JSON result for immediate service-specific decoding.
"""


class RpcInboundMessage(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    jsonrpc: Literal["2.0"]
    id: int | str | None = None
    method: str | None = None
    result: JsonValue = None
    error: JsonValue = None
