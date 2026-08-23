import XCTest

/**
 solid-name: CheckoutUITests
 solid-category: test
 solid-description: Exercises checkout UI behavior while exposing representative UI-test violations for workflow validation.
 */
final class CheckoutUITests: XCTestCase {
    private let app = XCUIApplication()

    override func setUp() {
        super.setUp()
        app.launch()
    }

    func testCheckoutTitle() {
        app.buttons["Shop"].tap()
        app.buttons["Cart"].tap()
        app.buttons["Checkout"].tap()
        Thread.sleep(forTimeInterval: 1)
        XCTAssertTrue(app.staticTexts["Checkout"].exists)
    }

    func testCheckoutButton() {
        app.buttons["Shop"].tap()
        app.buttons["Cart"].tap()
        app.buttons["Checkout"].tap()
        XCTAssertTrue(app.buttons["Pay"].exists)
    }
}
