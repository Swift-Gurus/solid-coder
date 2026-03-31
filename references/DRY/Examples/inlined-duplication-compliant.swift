// DRY-2 Compliant: Shared abstraction extracted
// The validate-transform-persist sequence is extracted into a generic function.

protocol Itemizable: Codable, Identifiable {
    var id: String { get }
    var items: [Item] { get }
    var total: Decimal { get }
    init(id: String, items: [Item], total: Decimal)
}

// ✅ Compliant: shared logic extracted behind a protocol

protocol ItemPersisting {
    func save<T: Itemizable>(_ entity: T, keyPrefix: String) throws
}

final class ItemPersistenceService: ItemPersisting {
    private let storage: StorageProviding

    init(storage: StorageProviding) {
        self.storage = storage
    }

    func save<T: Itemizable>(_ entity: T, keyPrefix: String) throws {
        guard !entity.items.isEmpty else { throw ValidationError.empty }
        guard entity.total > 0 else { throw ValidationError.invalidTotal }

        let normalized = entity.items.map { item in
            Item(name: item.name.trimmingCharacters(in: .whitespaces),
                 quantity: max(1, item.quantity),
                 price: item.price)
        }

        let updated = T(id: entity.id, items: normalized, total: entity.total)
        try storage.save(updated, forKey: "\(keyPrefix)-\(entity.id)")
    }
}

// Consumers depend on the protocol, not the concrete type

protocol OrderSaving {
    func saveOrder(_ order: Order) throws
}

final class OrderService: OrderSaving {
    private let persistence: ItemPersisting

    init(persistence: ItemPersisting) {
        self.persistence = persistence
    }

    func saveOrder(_ order: Order) throws {
        try persistence.save(order, keyPrefix: "order")
    }
}

protocol CartSaving {
    func saveCart(_ cart: Cart) throws
}

final class CartService: CartSaving {
    private let persistence: ItemPersisting

    init(persistence: ItemPersisting) {
        self.persistence = persistence
    }

    func saveCart(_ cart: Cart) throws {
        try persistence.save(cart, keyPrefix: "cart")
    }
}

// Analysis:
// - Validate-transform-persist sequence exists once in ItemPersistenceService
// - OrderService and CartService depend on ItemPersisting protocol (OCP compliant)
// - Dependencies injected via init (OCP compliant)
// - Inlined duplications: 0 → COMPLIANT
