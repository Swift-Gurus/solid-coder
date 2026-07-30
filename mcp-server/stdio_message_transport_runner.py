"""
solid-name: StdioMessageTransportRunner
solid-category: service
solid-description: Processes RPC messages and sends responses.
"""

from typing import Optional

from incoming_message_reading import IncomingMessageReading
from message_transport_running import MessageTransportRunning
from outgoing_message_factory import OutgoingMessageFactorying
from outgoing_message_writing import OutgoingMessageWriting
from rpc_dispatching import RpcDispatching
from stdout_sink import StdoutSink
from transport_format_detecting import TransportFormatDetecting


class StdioMessageTransportRunner(MessageTransportRunning):

    def __init__(
        self,
        incoming: IncomingMessageReading,
        stdout: StdoutSink,
        format_detector: TransportFormatDetecting,
        dispatcher: RpcDispatching,
        outgoing_factory: OutgoingMessageFactorying,
    ) -> None:
        self._incoming = incoming
        self._stdout = stdout
        self._format_detector = format_detector
        self._dispatcher = dispatcher
        self._outgoing_factory = outgoing_factory
        self._outgoing: Optional[OutgoingMessageWriting] = None

    def run(self) -> None:
        while True:
            msg = self._incoming.read_message()
            if msg is None:
                break
            self._ensure_outgoing()
            response = self._dispatcher.dispatch(msg.get("method", ""), msg.get("id"), msg.get("params", {}))
            if response is not None and self._outgoing is not None:
                self._outgoing.write_message(response)

    def _ensure_outgoing(self) -> None:
        if self._outgoing is not None:
            return
        first_byte = getattr(self._incoming, "detected_first_byte", None)
        if first_byte is None:
            return
        self._outgoing = self._outgoing_factory.create(self._stdout, self._format_detector, first_byte)
