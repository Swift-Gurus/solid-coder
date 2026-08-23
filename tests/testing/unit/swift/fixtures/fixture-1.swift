import XCTest

/**
 solid-name: CheckoutTests
 solid-category: test
 solid-description: Exercises checkout behavior while exposing representative unit-test violations for workflow validation.
 */
final class CheckoutTests: XCTestCase {
    static var sharedResult = false

    func test1() {
        let service = CheckoutService()
        if service.canCheckout {
            XCTAssertTrue(service.canCheckout)
        }
    }

    func testSave() {
        let service = CheckoutService()
        XCTAssertEqual(service.total, service.total)
    }

    func testBasic() {
        let mock = MockPriceFormatter()
        mock.formatted = "$10"
        XCTAssertEqual(mock.formatted, "$10")
    }
}

struct CheckoutService {
    let canCheckout = true
    let total = 10
}

final class MockPriceFormatter {
    var formatted = ""
}
