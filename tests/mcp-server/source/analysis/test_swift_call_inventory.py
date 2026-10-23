from source.analysis.tree_sitter_swift_inventory_parser_factory import (
    TreeSitterSwiftInventoryParserFactory,
)

"""
solid-name: test_swift_call_inventory
solid-category: unit-test
solid-spec: [SPEC-067]
solid-description: Verifies actual Swift call syntax and supporting source evidence without treating comments or literal text as invocations.
"""


def test_calls_preserve_direct_conditional_and_helper_evidence():
    source = """protocol Loading { func load() -> String }
class Loader: Loading {
    func load() -> String { parse() }
    private func parse() -> String {
        if invalid { Swift.fatalError("unsupported") }
        return "loaded"
    }
    init() { fatalError("unavailable") }
}
"""
    inventory = TreeSitterSwiftInventoryParserFactory().make().parse(source)

    assert [call.callee for call in inventory.calls] == [
        "parse",
        "Swift.fatalError",
        "fatalError",
    ]
    assert [call.span.start for call in inventory.calls] == [3, 5, 8]
    assert [call.expression for call in inventory.calls] == [
        "parse()",
        'Swift.fatalError("unsupported")',
        'fatalError("unavailable")',
    ]
    assert len({call.identity for call in inventory.calls}) == 3
    for call in inventory.calls:
        assert (
            source.encode()[call.start_offset : call.end_offset].decode()
            == call.expression
        )


def test_comments_literals_and_function_references_are_not_calls():
    source = """func example() {
    // fatalError("comment")
    /* fatalError("block comment") */
    let text = "fatalError(plain text)"
    let reference = fatalError
    let interpolated = "value: \\(fatalError("actual call"))"
}
"""
    inventory = TreeSitterSwiftInventoryParserFactory().make().parse(source)

    assert [call.expression for call in inventory.calls] == [
        'fatalError("actual call")'
    ]


def test_receiver_calls_retain_receiver_instead_of_assuming_global_function():
    source = 'func example() { logger.fatalError("message"); self.parse(value: 1) }'
    inventory = TreeSitterSwiftInventoryParserFactory().make().parse(source)

    assert [call.callee for call in inventory.calls] == [
        "logger.fatalError",
        "self.parse",
    ]
    assert inventory.calls[1].argument_labels == ["value"]


def test_callee_formatting_does_not_change_its_identity():
    source = 'func example() { Swift /* module */ . fatalError("unsupported") }'
    inventory = TreeSitterSwiftInventoryParserFactory().make().parse(source)

    assert [call.callee for call in inventory.calls] == ["Swift.fatalError"]
    assert (
        inventory.calls[0].expression
        == 'Swift /* module */ . fatalError("unsupported")'
    )
