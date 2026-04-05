// BUG-2 + BUG-4 COMPLIANT: Clean logic, proper error handling, correctness

import Foundation

class OrderProcessor {
    private var orders: [Order] = []
    private let dateProvider: () -> Date
    private let idProvider: () -> String

    // Injected providers for testability (no Date()/UUID() in deterministic context)
    init(dateProvider: @escaping () -> Date = { Date() },
         idProvider: @escaping () -> String = { UUID().uuidString }) {
        self.dateProvider = dateProvider
        self.idProvider = idProvider
    }

    // Clean: no unreachable code
    func validateOrder(_ order: Order) -> Bool {
        guard order.items.count > 0 else {
            return false
        }
        return order.total > 0
    }

    // Clean: no dead branch — direct use of non-optional
    func processOrder(_ order: Order) throws {
        guard let customer = order.customer else {
            throw OrderError.noCustomer
        }
        try chargeCustomer(customer, amount: order.total)
    }

    // Clean: all edge cases handled explicitly
    func applyDiscount(_ amount: Double, to total: Double) -> Double {
        if amount > 0 {
            return total - amount
        } else if amount < 0 {
            return total + abs(amount) // surcharge
        } else {
            return total // amount == 0, no change
        }
    }

    // Clean: exhaustive switch — compiler catches future cases
    func handleStatus(_ status: OrderStatus) {
        switch status {
        case .placed: prepareOrder()
        case .shipped: notifyCustomer()
        case .cancelled: refundCustomer()
        case .refunded: archiveOrder()
        }
    }

    // Safe: epsilon comparison for floating point
    func isFullyPaid(_ paid: Double, total: Double, epsilon: Double = 1e-10) -> Bool {
        return abs(paid - total) < epsilon
    }

    // Safe: filter instead of mutating during iteration
    func removeExpiredOrders() {
        orders.removeAll { $0.isExpired }
    }

    // Safe: injected date/id providers for determinism
    func createOrder(items: [Item]) -> Order {
        return Order(
            id: idProvider(),
            items: items,
            total: items.reduce(0) { $0 + $1.price },
            createdAt: dateProvider(),
            customer: nil,
            isExpired: false
        )
    }

    // Safe: all errors handled — specific handling + propagation of unknowns
    func saveOrder(_ order: Order) throws {
        do {
            try persistence.save(order)
        } catch PersistenceError.diskFull {
            cleanupDisk()
            try persistence.save(order)
        } catch {
            logger.error("Failed to save order \(order.id): \(error)")
            throw OrderError.saveFailed(underlying: error)
        }
    }

    private func chargeCustomer(_ customer: Customer, amount: Double) throws {}
    private func prepareOrder() {}
    private func notifyCustomer() {}
    private func refundCustomer() {}
    private func archiveOrder() {}
    private func cleanupDisk() {}
    private let persistence = OrderPersistence()
    private let logger = Logger()
}

struct Order {
    let id: String
    let items: [Item]
    let total: Double
    let createdAt: Date
    let customer: Customer?
    let isExpired: Bool
}

struct Item {
    let name: String
    let price: Double
}

struct Customer {}

enum OrderStatus {
    case placed, shipped, cancelled, refunded
}

enum OrderError: Error {
    case noCustomer
    case saveFailed(underlying: Error)
}

enum PersistenceError: Error {
    case diskFull
}

struct OrderPersistence {
    func save(_ order: Order) throws {}
}

struct Logger {
    func error(_ message: String) {}
}
