// TEST-2 Violation: try? silently swallows errors in tests
// Failures become invisible — test passes when it shouldn't.

import XCTest
@testable import MyApp

final class PaymentServiceTests: XCTestCase {

    // ❌ try? with fallback — hides the real failure reason
    func test_processPayment_withValidCard_succeeds() async {
        let service = PaymentService()
        let result = try? await service.processPayment(amount: 9.99)
            ?? PaymentResult.empty  // if processPayment throws, test silently uses .empty

        XCTAssertNotNil(result)  // always passes — fallback guarantees non-nil
    }
}

// Analysis:
// - All three tests hide failure causes behind try?
// - If the underlying code breaks, these tests still pass or produce vague failures
// - No stack trace, no error message, no signal about what went wrong
