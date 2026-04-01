// TEST-5 Compliant: Factory + builder pattern for SUT with 4 dependencies

import XCTest
@testable import MyApp

final class OrderServiceTests: XCTestCase {

    private var factory: OrderServiceSUTFactory!

    override func setUp() {
        super.setUp()
        factory = OrderServiceSUTFactory()
    }

    override func tearDown() {
        factory = nil
        super.tearDown()
    }

    private var sut: OrderService { factory.makeSUT() }

    func test_placeOrder_withValidCart_succeeds() async throws {
        factory.withStockAvailable()
        factory.withPaymentSucceeding()

        let order = try await sut.placeOrder(cart: .mock)

        XCTAssertEqual(order.status, .confirmed)
    }

    func test_placeOrder_withOutOfStock_throwsError() async {
        factory.withOutOfStock()

        do {
            _ = try await sut.placeOrder(cart: .mock)
            XCTFail("Expected out of stock error")
        } catch {
            XCTAssertTrue(error is InventoryError)
        }
    }
}

private final class OrderServiceSUTFactory {

    let network = MockNetworkClient()
    let payment = MockPaymentProcessor()
    let inventory = MockInventoryChecker()
    let notifier = MockNotificationSender()

    func makeSUT() -> OrderService {
        OrderService(
            network: network,
            payment: payment,
            inventory: inventory,
            notifier: notifier
        )
    }

    @discardableResult
    func withStockAvailable() -> Self {
        inventory.stockResult = true
        return self
    }

    @discardableResult
    func withOutOfStock() -> Self {
        inventory.stockResult = false
        return self
    }

    @discardableResult
    func withPaymentSucceeding() -> Self {
        payment.chargeResult = .success
        return self
    }
}

// Analysis:
// - Factory centralizes all 4 mock dependencies
// - Builder methods describe scenarios in domain language
// - Each test shows only the condition it cares about
// - TEST-5 setup complexity violations: 0
