"""Checks bounded semantic transport independently of an installed server."""

from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from unittest import TestCase
from unittest.mock import Mock

from content_length_reader import ContentLengthReader
from content_length_writer import ContentLengthWriter
from harness.pydantic_model_decoder import PydanticModelDecoder
from health.llama.timer import TimeMeasuring
from source.analysis.provenance.bounded_rpc_message_reader import (
    BoundedRpcMessageReader,
    TimedRpcMessageReading,
)
from source.analysis.provenance.rpc_inbound_message import RpcInboundMessage
from source.analysis.provenance.stdio_rpc_channel import StdioRpcChannel


class TestStdioRpcChannel(TestCase):
    def setUp(self):
        self.incoming = Mock(spec=TimedRpcMessageReading)
        self.timer = Mock(spec=TimeMeasuring)
        self.timer.now.return_value = 0
        self.output = BytesIO()
        self.channel = StdioRpcChannel(
            outgoing=self.output,
            reader=self.incoming,
            writer=ContentLengthWriter(),
            timer=self.timer,
            timeout_seconds=2,
        )

    def test_correlates_responses_after_notifications_and_peer_requests(self):
        self.incoming.read.side_effect = [
            RpcInboundMessage(jsonrpc="2.0", method="progress"),
            RpcInboundMessage(
                jsonrpc="2.0", id="peer", method="workspace/configuration"
            ),
            RpcInboundMessage(jsonrpc="2.0", id=1, result=["symbol"]),
        ]
        self.assertEqual(self.channel.request("lookup", None), ["symbol"])
        self.output.seek(0)
        decoder = PydanticModelDecoder(RpcInboundMessage)
        request = decoder.decode(
            ContentLengthReader().read(self.output, b""), "request"
        )
        rejection = decoder.decode(
            ContentLengthReader().read(self.output, b""), "rejection"
        )
        self.assertEqual(request.id, 1)
        self.assertEqual(rejection.id, "peer")
        self.assertIsNotNone(rejection.error)

    def test_deadline_applies_across_multiple_requests(self):
        self.incoming.read.return_value = RpcInboundMessage(jsonrpc="2.0", id=1)
        self.channel.request("first", None)
        self.timer.now.return_value = 3
        with self.assertRaisesRegex(TimeoutError, "second"):
            self.channel.request("second", None)
        self.assertEqual(self.incoming.read.call_count, 1)

    def test_worker_timeout_names_the_failed_request(self):
        self.incoming.read.side_effect = TimeoutError()
        with self.assertRaisesRegex(TimeoutError, "lookup"):
            self.channel.request("lookup", None)

    def test_closed_peer_is_not_an_empty_success(self):
        self.incoming.read.return_value = None
        with self.assertRaisesRegex(ConnectionError, "closed"):
            self.channel.request("lookup", None)

    def test_unrelated_response_is_rejected(self):
        self.incoming.read.return_value = RpcInboundMessage(jsonrpc="2.0", id=2)
        with self.assertRaisesRegex(ConnectionError, "unrelated"):
            self.channel.request("lookup", None)

    def test_peer_error_is_preserved(self):
        self.incoming.read.return_value = RpcInboundMessage(
            jsonrpc="2.0", id=1, error="missing context"
        )
        with self.assertRaisesRegex(ConnectionError, "missing context"):
            self.channel.request("lookup", None)


class TestBoundedRpcMessageReader(TestCase):
    def test_decodes_real_framing_and_eof(self):
        stream = BytesIO()
        ContentLengthWriter().write(stream, {"jsonrpc": "2.0", "id": 1, "result": []})
        stream.seek(0)
        with ThreadPoolExecutor(max_workers=1) as executor:
            reader = BoundedRpcMessageReader(
                incoming=stream,
                reader=ContentLengthReader(),
                decoder=PydanticModelDecoder(RpcInboundMessage),
                executor=executor,
            )
            self.assertEqual(reader.read(1).result, [])
            self.assertIsNone(reader.read(1))
