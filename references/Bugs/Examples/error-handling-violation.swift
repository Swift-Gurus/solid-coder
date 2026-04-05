// BUG-2 + BUG-4 VIOLATION: Logic bugs, error handling gaps, correctness issues

import Foundation

class OrderProcessor {
    private var orders: [Order] = []

    // BUG-2: unreachable code after return
    func validateOrder(_ order: Order) -> Bool {
        guard order.items.count > 0 else {
            return false
        }
        return order.total > 0
        print("Order validated: \(order.id)") // unreachable
    }

    // BUG-2: dead branch — condition always true after guard
    func processOrder(_ order: Order) throws {
        guard let customer = order.customer else {
            throw OrderError.noCustomer
        }
        // customer is non-optional here, `if let` is a dead branch
        if let customer = customer as? Customer {
            try chargeCustomer(customer, amount: order.total)
        }
    }

    // BUG-2: missing edge case — handles > 0 and < 0 but not == 0
    func applyDiscount(_ amount: Double, to total: Double) -> Double {
        if amount > 0 {
            return total - amount
        } else if amount < 0 {
            return total + abs(amount) // surcharge
        }
        // BUG: falls through with no return for amount == 0
        return total // only reached by accident
    }

    // BUG-2: empty default hides future enum cases
    func handleStatus(_ status: OrderStatus) {
        switch status {
        case .placed: prepareOrder()
        case .shipped: notifyCustomer()
        default: break // silently ignores .cancelled, .refunded, future cases
        }
    }

    // BUG-4: float equality — unreliable comparison
    func isFullyPaid(_ paid: Double, total: Double) -> Bool {
        return paid == total // 0.1 + 0.2 != 0.3
    }

    // BUG-4: mutation during iteration
    func removeExpiredOrders() {
        for (index, order) in orders.enumerated() {
            if order.isExpired {
                orders.remove(at: index) // mutating while iterating — crash
            }
        }
    }

    // BUG-4: Date() in deterministic context — breaks testability
    func createOrder(items: [Item]) -> Order {
        return Order(
            id: UUID().uuidString, // non-deterministic
            items: items,
            total: items.reduce(0) { $0 + $1.price },
            createdAt: Date(), // non-deterministic
            customer: nil,
            isExpired: false
        )
    }

    // BUG-4: incomplete catch — handles specific error, silently drops others
    func saveOrder(_ order: Order) {
        do {
            try persistence.save(order)
        } catch PersistenceError.diskFull {
            cleanupDisk()
            try? persistence.save(order)
        } catch {
            // all other errors silently dropped
        }
    }

    private func chargeCustomer(_ customer: Customer, amount: Double) throws {}
    private func prepareOrder() {}
    private func notifyCustomer() {}
    private func cleanupDisk() {}
    private let persistence = OrderPersistence()
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
}

enum PersistenceError: Error {
    case diskFull
}

struct OrderPersistence {
    func save(_ order: Order) throws {}
}
