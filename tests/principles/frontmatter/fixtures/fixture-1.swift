import Foundation

class PaymentValidator {
    func validate(_ amount: Double) -> Bool {
        amount > 0
    }
}
