"""Checks native-worker response correlation and failure propagation."""

from unittest import TestCase
from unittest.mock import Mock

from harness.pydantic_model_decoder import PydanticModelDecoder
from json_rpc_response_builder import JsonRpcResponseBuilder
from source.analysis.provenance.native.native_sourcekit_dispatcher import NativeSourceKitDispatcher
from source.analysis.provenance.native.native_sourcekit_request import NativeSourceKitRequest
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing


class TestNativeSourceKitDispatcher(TestCase):
    def setUp(self):
        self.requests = Mock(spec=SourceSyntaxParsing)
        self.dispatcher = NativeSourceKitDispatcher(
            PydanticModelDecoder(NativeSourceKitRequest), self.requests, JsonRpcResponseBuilder(),
        )

    def test_returns_native_response_with_original_request_id(self):
        self.requests.parse.return_value = "{key.usr: symbol}"
        result = self.dispatcher.dispatch("native", 7, {"payload": "query"})
        self.assertEqual(result, {"jsonrpc": "2.0", "id": 7, "result": "{key.usr: symbol}"})
        self.requests.parse.assert_called_once_with("query")

    def test_preserves_native_error_without_claiming_success(self):
        self.requests.parse.side_effect = ConnectionError("semantic provider unavailable")
        result = self.dispatcher.dispatch("native", 9, {"payload": "query"})
        self.assertEqual(result["id"], 9)
        self.assertIn("semantic provider unavailable", result["error"]["message"])
        self.assertNotIn("result", result)

    def test_unknown_methods_and_notifications_do_not_execute_native_requests(self):
        self.assertEqual(self.dispatcher.dispatch("other", 3, {})["error"]["code"], -32601)
        self.assertIsNone(self.dispatcher.dispatch("native", None, {}))
        self.requests.parse.assert_not_called()
