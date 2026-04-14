protocol PaymentMethod {
    func process(amount: Double) -> Bool
}

class PaymentProcessor {
    private let paymentMethod: PaymentMethod

    init(paymentMethod: PaymentMethod) {
        self.paymentMethod = paymentMethod
    }

    func processPayment(amount: Double) -> Bool {
        return paymentMethod.process(amount: amount)
    }
}

// Extension: new payment types added WITHOUT modifying PaymentProcessor

class CreditCardPayment: PaymentMethod {
    func process(amount: Double) -> Bool {
        print("Processing credit card: $\(amount)")
        return true
    }
}

class PayPalPayment: PaymentMethod {
    func process(amount: Double) -> Bool {
        print("Processing PayPal: $\(amount)")
        return true
    }
}

class BitcoinPayment: PaymentMethod {
    func process(amount: Double) -> Bool {
        print("Processing Bitcoin: $\(amount)")
        return true
    }
}

// Adding Apple Pay = new class, zero modification to existing code
class ApplePayPayment: PaymentMethod {
    func process(amount: Double) -> Bool {
        print("Processing Apple Pay: $\(amount)")
        return true
    }
}
