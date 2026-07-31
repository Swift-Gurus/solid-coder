import Foundation

/**
 solid-name: PaymentValidator
 solid-category: utility
 solid-description: Determines whether a payment amount is valid for processing.
 */
class PaymentValidator {
    func validate(_ amount: Double) -> Bool {
        amount > 0
    }
}
