// DRY-2 Violation: Inlined Duplication
// Same logical sequence appears in multiple locations.

// --- Features/Orders/OrderService.swift ---

protocol OrderSaving {
    func saveOrder(_ order: Order) throws
}

final class OrderService: OrderSaving {
    private let storage: StorageProviding

    init(storage: StorageProviding) {
        self.storage = storage
    }

    // 🔥 DRY-2 Violation: validate-transform-persist sequence duplicated
    func saveOrder(_ order: Order) throws {
        guard !order.items.isEmpty else { throw ValidationError.empty }
        guard order.total > 0 else { throw ValidationError.invalidTotal }

        let normalized = order.items.map { item in
            Item(name: item.name.trimmingCharacters(in: .whitespaces),
                 quantity: max(1, item.quantity),
                 price: item.price)
        }

        let updated = Order(id: order.id, items: normalized, total: order.total)
        try storage.save(updated, forKey: "order-\(order.id)")
    }
}

// --- Features/Cart/CartService.swift ---

protocol CartSaving {
    func saveCart(_ cart: Cart) throws
}

final class CartService: CartSaving {
    private let storage: StorageProviding

    init(storage: StorageProviding) {
        self.storage = storage
    }

    // 🔥 DRY-2 Violation: same validate-transform-persist sequence
    func saveCart(_ cart: Cart) throws {
        guard !cart.items.isEmpty else { throw ValidationError.empty }
        guard cart.total > 0 else { throw ValidationError.invalidTotal }

        let normalized = cart.items.map { item in
            Item(name: item.name.trimmingCharacters(in: .whitespaces),
                 quantity: max(1, item.quantity),
                 price: item.price)
        }

        let updated = Cart(id: cart.id, items: normalized, total: cart.total)
        try storage.save(updated, forKey: "cart-\(cart.id)")
    }
}

// Analysis:
// - OrderService.saveOrder and CartService.saveCart: STRUCTURAL match
//   Same algorithm: validate emptiness → validate total → normalize items → persist
//   Different types (Order vs Cart) but identical logical sequence
// - Inlined duplications: 1 → SEVERE
