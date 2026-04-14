// TEST-5 Violation: Inline SUT construction with 4 mocks repeated across tests

import XCTest
@testable import MyApp

final class OrderServiceTests: XCTestCase {

    func test_placeOrder_withValidCart_succeeds() async throws {
        let mockNetwork = MockNetworkClient()
        let mockPayment = MockPaymentProcessor()
        let mockInventory = MockInventoryChecker()
        let mockNotifier = MockNotificationSender()
        let sut = OrderService(
            network: mockNetwork,
            payment: mockPayment,
            inventory: mockInventory,
            notifier: mockNotifier
        )

        mockInventory.stockResult = true
        mockPayment.chargeResult = .success

        let order = try await sut.placeOrder(cart: .mock)
        XCTAssertEqual(order.status, .confirmed)
    }

    func test_placeOrder_withOutOfStock_throwsError() async {
        let mockNetwork = MockNetworkClient()
        let mockPayment = MockPaymentProcessor()
        let mockInventory = MockInventoryChecker()
        let mockNotifier = MockNotificationSender()
        let sut = OrderService(
            network: mockNetwork,
            payment: mockPayment,
            inventory: mockInventory,
            notifier: mockNotifier
        )

        mockInventory.stockResult = false

        do {
            _ = try await sut.placeOrder(cart: .mock)
            XCTFail("Expected out of stock error")
        } catch {
            XCTAssertTrue(error is InventoryError)
        }
    }
}

// Analysis:
// - Identical 4-mock construction block repeated in both tests
// - Each test only varies 1-2 mock configurations but rebuilds everything
// - TEST-5 setup complexity violations: 2
