"""Exchanges bounded JSON-RPC requests over framed process streams."""

from typing import BinaryIO, Protocol

from pydantic import JsonValue

from health.llama.timer import TimeMeasuring
from message_writing import MessageWriting
from source.analysis.provenance.bounded_rpc_message_reader import TimedRpcMessageReading


"""
solid-name: RpcExchanging
solid-category: abstraction
solid-spec: [SPEC-064]
solid-description: Contract for exchanging requests and notifications with a JSON-RPC peer.
"""
class RpcExchanging(Protocol):
    def request(self, method: str, params: JsonValue) -> JsonValue: ...
    def notify(self, method: str, params: JsonValue) -> None: ...


"""
solid-name: StdioRpcChannel
solid-category: boundary-adapter
solid-spec: [SPEC-064]
solid-description: Exchanges correlated requests with a peer within a bounded session.
"""
class StdioRpcChannel(RpcExchanging):
    def __init__(
        self,
        outgoing: BinaryIO,
        reader: TimedRpcMessageReading,
        writer: MessageWriting,
        timer: TimeMeasuring,
        timeout_seconds: float,
    ) -> None:
        self._outgoing = outgoing
        self._reader = reader
        self._writer = writer
        self._timer = timer
        self._deadline = timer.now() + timeout_seconds
        self._sequence = 0

    def request(self, method: str, params: JsonValue) -> JsonValue:
        self._sequence += 1
        self._writer.write(self._outgoing, {
            "jsonrpc": "2.0", "id": self._sequence,
            "method": method, "params": params,
        })
        while True:
            remaining = self._deadline - self._timer.now()
            if remaining <= 0:
                raise TimeoutError(f"Semantic service timed out during {method}.")
            try:
                message = self._reader.read(remaining)
            except TimeoutError as error:
                raise TimeoutError(f"Semantic service timed out during {method}.") from error
            if message is None:
                raise ConnectionError(f"Semantic service closed during {method}.")
            if message.method is not None:
                if message.id is not None:
                    self._writer.write(self._outgoing, {
                        "jsonrpc": "2.0", "id": message.id,
                        "error": {"code": -32601, "message": "Unsupported client capability"},
                    })
                continue
            if message.id != self._sequence:
                raise ConnectionError("Semantic service returned an unrelated response ID.")
            if message.error is not None:
                raise ConnectionError(f"Semantic service rejected {method}: {message.error}")
            return message.result

    def notify(self, method: str, params: JsonValue) -> None:
        self._writer.write(self._outgoing, {
            "jsonrpc": "2.0", "method": method, "params": params,
        })
