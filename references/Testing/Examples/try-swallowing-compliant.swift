// TEST-2 Compliant: Throwing try in tests — failures surface with full context

import XCTest
@testable import MyApp

final class PaymentServiceTests: XCTestCase {

    func test_processPayment_withValidCard_succeeds() async throws {
        let service = PaymentService()
        let result = try await service.processPayment(amount: 9.99)

        XCTAssertEqual(result.status, .success)
    }
}

// Analysis:
// - Throwing try — failure shows exact error and stack trace
// - No silent fallbacks, no skipped assertions
