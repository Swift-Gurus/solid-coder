import Foundation

protocol OrderStoring {
    func save(_ order: Data, id: String)
    func load(id: String) -> Data?
    func remove(id: String)
    func exists(id: String) -> Bool
}

class OrderRepository {
    private let store: OrderStoring

    init(store: OrderStoring) {
        self.store = store
    }

    func save(_ order: Data, id: String) {
        store.save(order, id: id)
    }

    func load(id: String) -> Data? {
        store.load(id: id)
    }

    func remove(id: String) {
        store.remove(id: id)
    }

    func exists(id: String) -> Bool {
        store.exists(id: id)
    }
}
