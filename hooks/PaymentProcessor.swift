/**
solid-description: Processes payments and issues refunds for financial transactions.
solid-category: service
*/

protocol PaymentGateway {
    func charge(amount: Decimal, currency: String, token: String) throws -> String
    func refund(transactionId: String, amount: Decimal) throws
}

class PaymentProcessor {
    private let gateway: PaymentGateway

    init(gateway: PaymentGateway) {
        self.gateway = gateway
    }

    func processPayment(amount: Decimal, currency: String, token: String) throws -> String {
        return try gateway.charge(amount: amount, currency: currency, token: token)
    }

    func issueRefund(transactionId: String, amount: Decimal) throws {
        try gateway.refund(transactionId: transactionId, amount: amount)
    }
}


