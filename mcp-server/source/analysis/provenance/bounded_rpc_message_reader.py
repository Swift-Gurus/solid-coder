"""Reads typed peer messages under a caller-owned deadline."""

from concurrent.futures import Executor
from typing import BinaryIO, Protocol

from harness.structured_model_decoding import StructuredModelDecoding
from message_reading import MessageReading
from source.analysis.provenance.rpc_inbound_message import RpcInboundMessage

"""
solid-name: TimedRpcMessageReading
solid-category: abstraction
solid-spec: [SPEC-064]
solid-description: Contract for receiving a typed peer message within a requested time budget.
"""


class TimedRpcMessageReading(Protocol):
    def read(self, timeout_seconds: float) -> RpcInboundMessage | None: ...


"""
solid-name: BoundedRpcMessageReader
solid-category: boundary-adapter
solid-spec: [SPEC-064]
solid-description: Receives a typed peer message within a requested time budget.
"""


class BoundedRpcMessageReader(TimedRpcMessageReading):
    def __init__(
        self,
        incoming: BinaryIO,
        reader: MessageReading,
        decoder: StructuredModelDecoding[RpcInboundMessage],
        executor: Executor,
    ) -> None:
        self._incoming = incoming
        self._reader = reader
        self._decoder = decoder
        self._executor = executor

    def read(self, timeout_seconds: float) -> RpcInboundMessage | None:
        future = self._executor.submit(self._reader.read, self._incoming, b"")
        raw = future.result(timeout=timeout_seconds)
        return (
            None
            if raw is None
            else self._decoder.decode(raw, "semantic-service response")
        )
